use std::cell::OnceCell;
use std::error::Error;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use crate::tree::Tree;

mod tree;

// static mut URLS: Option<Tree<String, PyObject>> = None;

#[derive(Debug)]
#[pyclass]
struct Urls {
    urls: OnceCell<Tree<String, PyObject>>, 
}

impl Urls {
    fn parse_urls_dict(py_urls: &PyDict) -> Self {
        fn create(p_urls: &PyDict) -> Tree<String, PyObject> {
            let gil = unsafe { Python::assume_gil_acquired() };

            let mut urls: Tree<String, PyObject> = Tree::new(gil.Ellipsis());

            for (key, value) in p_urls.iter() {
                if value.is_exact_instance_of::<PyDict>() {
                    match value.downcast::<PyDict>() {
                        Ok(p_dict) => {
                            urls.entry(key.to_string()).or_insert(create(p_dict));
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
            return urls
        }
        let final_urls = create(py_urls);
        let cell = OnceCell::new();
        cell.set(final_urls).expect("failed to create OneCell");
        Self { urls: cell }
    }

    fn finding_endpoint(&self, path: String) -> Option<(PyObject, String)> {
        let path: String = clean_path(path);
        let parts: Vec<&str> = path.split('/').collect();

        match self.urls.get() {
           Some(tree) => {
                let a = tree.iter().last().unwrap();
                return Some((tree.iter().last().unwrap().1.clone() , a.0.iter().last().unwrap().to_owned().to_owned()));
                    // return Some((tree[parts.first().unwrap().to_owned()].value.clone(), parts.last().unwrap().to_owned().to_string()))
            },
            None => return None,
        }
           
        // for (i, part) in parts.iter().enumerate() {
        //     let last_path: bool = (i + 1) == parts_len;
        //
        //     let mut urls_ref: &Urls = self.urls.get().unwrap().iter;
        //     match urls_ref.urls.get() {
        //         Some(found) => {
        //             if is_dict(&found.value) == false {
        //                 return if last_path {
        //                     found_path = push_path(found_path, part.to_string());
        //                     Some((found.clone().value, found_path.to_string()))
        //                 } else {
        //                     None
        //                 };
        //             }
        //             if is_dict(&found.value) {
        //                 if last_path {
        //                     return match found.get("") {
        //                         Some(inner_found) => {
        //                             if is_dict(&inner_found.value) == false {
        //                                 found_path = push_path(found_path, part.to_string());
        //                                 Some((inner_found.clone().value, found_path.to_string()))
        //                             } else {
        //                                 None
        //                             }
        //                         }
        //                         None => { None }
        //                     };
        //                 } else {
        //                     found_path = push_path(found_path, part.to_string());
        //                     urls_ref = &Urls { urls: found };
        //                     continue;
        //                 }
        //             }
        //         }
        //         None => {
        //             for (_key, _v) in self.urls.get().into_iter() {
        //                 if _key.len() == 0 {
        //                     continue;
        //                 }
        //                 let key = _key.get(0).unwrap();
        //
        //                 if key.starts_with('<') {
        //                     let value = urls.get(*key).unwrap();
        //
        //                     println!("value: {:?}", value);
        //                     if last_path {
        //                         if is_dict(&value.value) == false {
        //                             found_path = push_path(found_path, key.to_string());
        //                             return Some((value.clone().value, found_path.to_string()));
        //                         } else if is_dict(&value.value) {
        //                             match value.get("") {
        //                                 Some(inner_found) => {
        //                                     if is_dict(&inner_found.value) == false {
        //                                         found_path = push_path(found_path, key.to_string());
        //                                         return Some((inner_found.clone().value, found_path.to_string()));
        //                                     }
        //                                 }
        //                                 None => {}
        //                             };
        //                         }
        //                     } else if is_dict(&value.value) == false {
        //                         return None;
        //                     } else if is_dict(&value.value) {
        //                         found_path = push_path(found_path, key.to_string());
        //                         urls = value.clone();
        //                         break;
        //                     }
        //                 } else {
        //                     return None;
        //                 }
        //             }
        //         }
        //     }
        // }
    }
}

#[pyfunction]
fn find_endpoint(urls: &Urls, path: String) -> Option<(PyObject, String)> {
    match urls.finding_endpoint(path.to_string()) {
        None => { None }
        Some(result) => { Some(result) }
    }
}

#[pyfunction]
fn initialize_routing(py_urls: &PyDict) -> Urls {
    let urls = Urls::parse_urls_dict(py_urls);
    urls
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


fn push_path(mut path: String, part: String) -> String {
    path.push_str(&part);
    path.push('/');
    path
}



#[pymodule]
fn panther_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_endpoint, m)?)?;
    m.add_function(wrap_pyfunction!(initialize_routing, m)?)?;

    Ok(())
}


// fn is_callable(value: PyObject) -> bool {
//     value.is_callable()
// }

// fn is_dict(value: &Py<PyAny>) -> bool {
//     Python::with_gil(|py| {
//         value.is_instance::<PyDict>(py)
//     })
// }
