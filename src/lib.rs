use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use crate::tree::Tree;

mod tree;

static mut URLS: Option<Tree<String, PyObject>> = None;


fn parse_urls_dict(py_urls: &PyDict) -> Tree<String, PyObject> {
    let gil = unsafe { Python::assume_gil_acquired() };

    let mut urls: Tree<String, PyObject> = Tree::new(gil.Ellipsis());

    for (key, value) in py_urls.iter() {
        if value.is_exact_instance_of::<PyDict>() {
            match value.downcast::<PyDict>() {
                Ok(py_dict) => {
                    urls.entry(key.to_string()).or_insert(parse_urls_dict(py_dict));
                }
                Err(_) => {}
            }
        } else {
            match value.extract::<PyObject>() {
                Ok(object) => {
                    urls.entry(key.to_string()).or_insert(Tree::new(object));
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

// fn is_callable(value: PyObject) -> bool {
//     value.is_callable()
// }

fn is_dict(value: &Py<PyAny>) -> bool {
    Python::with_gil(|py| {
        value.is_instance::<PyDict>(py)
    })
}

fn push_path(mut path: String, part: String) -> String {
    path.push_str(&part);
    path.push('/');
    path
}

fn finding_endpoint(mut urls: Tree<String, PyObject>, path: String) -> Option<(PyObject, String)> {
    let path: String = clean_path(path);
    let parts: Vec<&str> = path.split('/').collect();
    let parts_len: usize = parts.len();

    let mut found_path = String::new();
    for (i, part) in parts.iter().enumerate() {
        let last_path: bool = (i + 1) == parts_len;

        let borrowed_url = urls.clone();
        match urls.get(*part) {
            Some(found) => {
                if is_dict(&found.value) == false {
                    return if last_path {
                        found_path = push_path(found_path, part.to_string());
                        Some((found.clone().value, found_path.to_string()))
                    } else {
                        None
                    };
                }
                if is_dict(&found.value) {
                    if last_path {
                        return match found.get("") {
                            Some(inner_found) => {
                                if is_dict(&inner_found.value) == false {
                                    found_path = push_path(found_path, part.to_string());
                                    Some((inner_found.clone().value, found_path.to_string()))
                                } else {
                                    None
                                }
                            }
                            None => { None }
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
                    if _key.len() == 0 {
                        continue;
                    }
                    let key = _key.get(0).unwrap();

                    if key.starts_with('<') {
                        let value = urls.get(*key).unwrap();

                        println!("value: {:?}", value);
                        if last_path {
                            if is_dict(&value.value) == false {
                                found_path = push_path(found_path, key.to_string());
                                return Some((value.clone().value, found_path.to_string()));
                            } else if is_dict(&value.value) {
                                match value.get("") {
                                    Some(inner_found) => {
                                        if is_dict(&inner_found.value) == false {
                                            found_path = push_path(found_path, key.to_string());
                                            return Some((inner_found.clone().value, found_path.to_string()));
                                        }
                                    }
                                    None => {}
                                };
                            }
                        } else if is_dict(&value.value) == false {
                            return None;
                        } else if is_dict(&value.value) {
                            found_path = push_path(found_path, key.to_string());
                            urls = value.clone();
                            break;
                        }
                    } else {
                        return None;
                    }
                }
            }
        }
    }

    return None;
}

#[pyfunction]
fn find_endpoint(path: &PyString) -> Option<(PyObject, String)> {
    let urls = unsafe { URLS.clone() }.unwrap();
    match finding_endpoint(urls, path.to_string()) {
        None => { None }
        Some(result) => { Some(result) }
    }
}

#[pymodule]
fn panther_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_endpoint, m)?)?;
    m.add_function(wrap_pyfunction!(initialize_routing, m)?)?;

    Ok(())
}