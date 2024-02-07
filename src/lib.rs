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
    // Strip '/'
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

fn finding_endpoint(mut urls: Tree<String, i32>, path: String) -> (i32, String) {
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
                if is_callable(found.value) {
                    return if last_path {
                        found_path = push_path(found_path, part.to_string());
                        (found.value, found_path.to_string())
                    } else {
                        endpoint_not_found
                    };
                }
                if is_subtree(found.value) {
                    if last_path {
                        return match found.get("") {
                            Some(inner_found) => {
                                if is_callable(inner_found.value) {
                                    found_path = push_path(found_path, part.to_string());
                                    (inner_found.value, found_path.to_string())
                                } else {
                                    endpoint_not_found
                                }
                            }
                            None => { endpoint_not_found }
                        };
                    } else {
                        found_path = push_path(found_path, part.to_string());
                        urls = found.clone();
                        continue;
                    }
                }
            }
            None => {

                for (_key, _v) in borrowed_url.iter() {
                    if _key.len() == 0{
                        continue;
                    }
                    let key = _key.get(0).unwrap();

                    if key.starts_with('<') {
                        let value = urls.get(*key).unwrap();

                        println!("value: {:?}", value);
                        if last_path{
                            if is_callable(value.value) {
                                found_path = push_path(found_path, key.to_string());
                                return (value.value, found_path.to_string());

                            } else if is_subtree(value.value) {
                                match value.get("") {
                                    Some(inner_found) => {
                                        if is_callable(inner_found.value) {
                                            found_path = push_path(found_path, key.to_string());
                                            return (inner_found.value, found_path.to_string());
                                        }
                                    }
                                    None => {}
                                };
                            }
                        } else if is_callable(value.value) {
                            return endpoint_not_found

                        } else if is_subtree(value.value) {
                            found_path = push_path(found_path, key.to_string());
                            urls = value.clone();
                            break
                        }
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
    let (endpoint, _found_path) = finding_endpoint(unsafe { URLS.clone() }.unwrap(), path.to_string());
    endpoint
}

#[pymodule]
fn panther_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_endpoint, m)?)?;
    m.add_function(wrap_pyfunction!(initialize_routing, m)?)?;

    Ok(())
}