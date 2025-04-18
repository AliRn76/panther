use std::collections::HashMap;
use once_cell::sync::OnceCell;
use pyo3::prelude::*;
use pyo3::types::PyDict;

static GLOBAL_ROUTES: OnceCell<RouteNode> = OnceCell::new();

#[derive(Debug, Clone)]
#[pyclass(module = "routing")]
pub struct RouteNode {
    #[pyo3(get)]
    handler: Option<Py<PyAny>>,

    static_children: HashMap<String, RouteNode>,
    param_child: Option<(String, Box<RouteNode>)>,
}
impl Default for RouteNode {      fn default() -> Self {          Self::new()      }  }
impl RouteNode {
    pub fn new() -> Self {
        RouteNode {
            handler: None,
            static_children: HashMap::new(),
            param_child: None,
        }
    }

    pub fn add_route(&mut self, py: Python, path: &str, handler: Py<PyAny>) {
        let segments: Vec<&str> = path
            .trim_matches('/')
            .split('/')
            .filter(|s| !s.is_empty())
            .collect();
        let mut node = self;
        for (i, &seg) in segments.iter().enumerate() {
            let is_last = i + 1 == segments.len();
            if seg.starts_with('<') && seg.ends_with('>') {
                let name = seg[1..seg.len()-1].to_string();
                let child = node.param_child.get_or_insert_with(|| {
                    (name.clone(), Box::new(RouteNode::new()))
                });
                node = child.1.as_mut();
                if is_last {
                    node.handler = Some(handler.clone_ref(py));
                }
            } else {
                let child = node
                    .static_children
                    .entry(seg.to_string())
                    .or_insert_with(RouteNode::new);
                node = child;
                if is_last {
                    node.handler = Some(handler.clone_ref(py));
                }
            }
        }
    }

    pub fn from_pyany(py: Python, obj: &PyAny) -> PyResult<Self> {
        let dict: &PyDict = obj.downcast::<PyDict>()
            .map_err(|_| PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                "Expected a dict of {str: callable}"
            ))?;
        let mut root = RouteNode::new();
        for (key, val) in dict.iter() {
            let path: String = key.extract()?;
            let handler: Py<PyAny> = val.into();
            root.add_route(py, &path, handler);
        }
        Ok(root)
    }

    /// Try to match `path`. If matched, return (handler, pattern_string).
    pub fn match_route_with_pattern(
        &self,
        path: &str,
    ) -> Option<(Py<PyAny>, String)> {
        let mut node = self;
        let mut pattern_parts = Vec::new();

        for seg in path.trim_matches('/').split('/') {
            if let Some(child) = node.static_children.get(seg) {
                pattern_parts.push(seg.to_string());
                node = child;
            } else if let Some((ref name, ref boxed)) = node.param_child {
                pattern_parts.push(format!("<{}>", name));
                node = boxed;
            } else {
                return None;
            }
        }

        node.handler.clone().map(|h| {
            let pat = pattern_parts.join("/");
            (h, pat)
        })
    }
}

/// Parse the Python dict into the global router.
#[pyfunction]
pub fn parse(py: Python, obj: &PyAny) -> PyResult<RouteNode> {
    let parsed = RouteNode::from_pyany(py, obj)?;
    GLOBAL_ROUTES
        .set(parsed.clone())
        .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
            "GLOBAL_ROUTES was already initialized"
        ))?;
    Ok(parsed)
}

#[pyfunction]
pub fn get(py: Python, path: &str) -> PyResult<(Option<Py<PyAny>>, String)> {
    let root = GLOBAL_ROUTES
        .get()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
            "GLOBAL_ROUTES is not initialized"
        ))?;

    if let Some((handler, pattern)) = root.match_route_with_pattern(path) {
        Ok((Some(handler.clone_ref(py)), pattern))
    } else {
        Ok((None, String::new()))
    }
}

/// The Python module definition.
#[pymodule]
#[pyo3(name = "panther_core")]
fn routing(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<RouteNode>()?;
    m.add_function(wrap_pyfunction!(parse, m)?)?;
    m.add_function(wrap_pyfunction!(get, m)?)?;
    Ok(())
}
