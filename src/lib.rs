#![allow(unused)]

use pyo3::prelude::*;
use pyo3::PyResult;
use pyo3::types::PyDict;

use std::sync::RwLock;
use std::sync::Arc;
use crate::tree::Tree;

mod tree;

#[derive(Debug, Clone, PartialEq, Eq, core::hash::Hash)]
enum Routing {
    Param(String),
    Route(String),
}

#[derive(Debug, Clone)]
#[pyclass(module = "routing")]
pub struct Urls {
    urls: TreeRef,
}

type TreeRef = Arc<RwLock<Tree<Routing, Option<Py<PyAny>>>>>;

#[pymethods]
impl Urls {

    #[new]
    fn parse_urls_dict(urls: &PyDict) -> PyResult<Self> {
        let mut tree: TreeRef = Arc::new(RwLock::new(Tree::new(None)));
        let pydata: &PyDict = urls.downcast()?;

        fn create(dict: &PyDict, subtree: TreeRef) -> Option<TreeRef> {
            for (k, v) in dict.into_iter() {
                // println!("{:?},\n\n {:?}\n\n", &k, &v);
                let key = k.extract::<String>().unwrap();

                if !v.is_exact_instance_of::<PyDict>() {
                    println!("is Obj: {:?}", &v);
                    if key.chars().next() == Some('<') {
                        subtree.write().unwrap().entry(Routing::Param(key));
                    } else {
                        subtree.write().unwrap().entry(Routing::Route(key));
                    }
                    subtree.write().unwrap().value = Some(Py::from(v));
                    return Some(subtree.clone());
                } else {
                    let mut st: TreeRef = Arc::new(RwLock::new(Tree::new(None)));
                    let sa = create(v.extract::<&PyDict>().unwrap(), st.clone());
                    println!("is Dict: {:?}", v.extract::<&PyDict>().unwrap());
                    if key.chars().next() == Some('<') {
                        subtree.write().unwrap().entry(Routing::Param(key)).or_insert(st.clone());
                    } else {
                        subtree.write().unwrap().entry(Routing::Route(key)).or_insert(st.clone());
                    }
                    return match sa {
                        Some(res) => Some(res),
                        None => None,
                    }
                }
            }
            return None;
        }
        create(urls, tree.clone());
        Ok(Self { urls: tree })
    }

    fn print(&self) {
        println!("\n\n\n\n{:?}", self.urls)
    }

    fn finding_endpoint(&self, path: String) -> Option<(PyObject, String)> {
        let path: String = clean_path(path);
        let parts: Vec<&str> = path.split('/').collect();

        todo!()
        // match self.urls.get() {
        //    Some(tree) => {
        //         let a = tree.iter().last().unwrap();
        //         return Some((tree.iter().last().unwrap().1.clone() , a.0.iter().last().unwrap().to_owned().to_owned()));
        //     },
        //     None => return None,
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
fn panther_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Urls>()?;

    Ok(())
}
