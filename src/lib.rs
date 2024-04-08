#![allow(unused)]

use pyo3::prelude::*;
use pyo3::PyResult;
use pyo3::types::PyDict;

use std::sync::Arc;
use std::collections::{HashMap, VecDeque};
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

type TreeRef = Arc<Tree<Routing, Option<Py<PyAny>>>>;

#[pymethods]
impl Urls {

    #[new]
    fn parse_urls_dict(urls: &PyDict) -> PyResult<Self> {
        let mut vq = VecDeque::new();
        let pydata: &PyDict = urls.downcast()?;
        #[derive(Debug)]
        struct Rout{
            key: Routing,
            obj: Option<Py<PyAny>>,
        };

        fn create(dict: &PyDict, vq: &mut VecDeque<Rout>) {
            for (k, v) in dict.into_iter() {
                let key = k.extract::<String>().unwrap();

                if !v.is_exact_instance_of::<PyDict>() {
                    if key.chars().next() == Some('<') {
                        vq.push_front( Rout {
                            key: Routing::Param(key),
                            obj: Some(v.into()),
                        } );
                    } else {
                        vq.push_front( Rout {
                            key: Routing::Route(key),
                            obj: Some(v.into()),
                        } );
                    }
                } else {
                    if key.chars().next() == Some('<') {
                        vq.push_front( Rout {
                            key: Routing::Param(key),
                            obj: None,
                        } );
                    } else {
                        vq.push_front( Rout {
                            key: Routing::Route(key),
                            obj: None,
                        } );
                    }
                    create(v.extract::<&PyDict>().unwrap(), vq);
                }
            }
        }
        create(urls, &mut vq);
        let mut tree = Tree::new(None);
        let mut map = HashMap::new();
        for r in vq.iter() {
            if let Some(v) = &r.obj {
                map.insert(r.key.clone(), Arc::new(Tree::new(Some(v.clone()))));
            } else {
                tree = Tree::new(None);
                tree.subtrees = map;
                map = HashMap::new();
                map.insert(r.key.clone(), tree.clone().into());

            }
        }
        if !map.is_empty() {
            tree = Tree::new(None);
            tree.subtrees = map;
        }
        let tree_ref: TreeRef = Arc::new(tree);
        println!("{:?}", &vq);
        Ok(Self { urls: tree_ref })
    }

    fn print(&self) {
        println!("\n\n\n\n{:?}", self.urls)
    }

    fn finding_endpoint(&self, path: String) -> Option<(PyObject, String)> {
        let path: String = clean_path(path);
        let parts: Vec<&str> = path.split('/').collect();

        todo!()
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
