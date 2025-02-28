use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use crate::tree::Tree;

mod tree;

static mut URLS: Option<Tree<String, i32>> = None;


fn parse_urls_dict(py_urls: &PyDict) -> Tree<String, i32> {
    let mut urls: Tree<String, i32> = Tree::new(0);

    for (key, value) in py_urls.iter() {
        if value.is_exact_instance_of::<PyDict>() {
            match value.downcast::<PyDict>() {
                Ok(py_dict) => {
                    urls.entry(key.to_string()).or_insert(parse_urls_dict(py_dict));
                }
                Err(_) => {}
            }
        } else {
            match value.extract::<i32>() {
                Ok(integer_value) => {
                    urls.entry(key.to_string()).or_insert(Tree::new(integer_value));
                }
                Err(_) => {}
            }
        }
    }
    return urls.clone();
}

#[pyfunction]
fn initialize_routing(py_urls: &PyDict) {
    let urls = parse_urls_dict(py_urls);
    unsafe { URLS = Some(urls); }
}

fn clean_path(raw_path: String) -> String {
    let mut path: String = String::new();
    // Remove Query Params
    for char in raw_path.chars() {
        if char == '?' { break; }
        path.push(char);
    }
    // Remove '/' suffix & prefix
    path.trim_end_matches('/').trim_start_matches('/').to_string()
}

fn is_callable(value: i32) -> bool {
    value != 0
}

fn is_subtree(value: i32) -> bool {
    value == 0
}

fn push_path(mut path: String, part: String) -> String {
    path.push_str(&part);
    path.push('/');
    path
}


fn finding(mut urls: Tree<String, i32>, path: String) -> (i32, String) {
    let endpoint_not_found: (i32, String) = (-1, "".to_string());

    let path: String = clean_path(path);
    let parts: Vec<&str> = path.split('/').collect();
    let parts_len: usize = parts.len();

    let mut found_path = String::new();
    for (i, part) in parts.iter().enumerate() {
        let last_path: bool = (i + 1) == parts_len;

        let borrowed_url = urls.clone();
        match urls.get(*part) {
            Some(found) => {
                if last_path && is_callable(found.value) {
                    found_path = push_path(found_path, part.to_string());
                    return (found.value, found_path.to_string());
                }
                if is_subtree(found.value) {
                    found_path = push_path(found_path, part.to_string());

                    match found.get("") {
                        Some(inner_found) => {
                            if last_path && is_callable(inner_found.value) {
                                return (inner_found.value, part.to_string());
                            }
                        }
                        None => {}
                    }
                    urls = found.clone();
                    continue;
                }
            }
            None => {
                for (key, _value) in borrowed_url
                    .iter()
                    .filter_map(|(p, q)| {
                        if !p.is_empty() && p.get(0).unwrap().starts_with('<') {
                            Some((p.get(0).unwrap().clone(), q))
                        } else { None }
                    })
                {
                    let found = urls.get(key).unwrap();

                    if last_path {
                        if is_callable(found.value) {
                            found_path = push_path(found_path, key.to_string());
                            return (found.value, found_path.to_string());
                        }
                        if is_subtree(found.value) {
                            found_path = push_path(found_path, key.to_string());

                            match found.get("") {
                                Some(inner_found) => {
                                    if last_path && is_callable(inner_found.value) {
                                        return (inner_found.value, key.to_string());
                                    }
                                }
                                None => {}
                            }
                            urls = found.clone();
                            break;
                        }
                        return endpoint_not_found;
                    } else if is_subtree(found.value) {
                        urls = found.clone();
                        found_path = push_path(found_path, key.to_string());
                        break;
                    } else {
                        return endpoint_not_found;
                    }
                }
            }
        }
    }

    return endpoint_not_found;
}

#[pyfunction]
fn find_endpoint(path: &PyString) -> i32 {
    let (endpoint, _found_path) = finding(unsafe { URLS.clone() }.unwrap(), path.to_string());
    endpoint
}

#[pymodule]
fn panther_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_endpoint, m)?)?;
    m.add_function(wrap_pyfunction!(initialize_routing, m)?)?;

    Ok(())
}