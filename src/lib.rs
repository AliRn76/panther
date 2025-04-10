use std::collections::HashMap;
use std::rc::Rc;
use pyo3::prelude::*;
use pyo3::PyResult;
use pyo3::types::PyDict;
use std::sync::OnceLock;
use pyo3::exceptions::PyValueError;

// Global static storage for parsed URL routes
static GLOBAL_ROUTES: OnceLock<Url> = OnceLock::new();

#[derive(Debug, Clone)]
#[pyclass(module = "routing")]
pub struct Url {
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub handler: Option<Py<PyAny>>,
    #[pyo3(get)]
    pub inner: HashMap<String, Url>,
}

impl Url {
    /// Recursively parses a PyAny (expected to be a dict or a leaf handler)
    /// into a Url node with the given name.
    fn from_pyany(py: Python, obj: &PyAny, name: String) -> PyResult<Self> {
        let mut url = Url {
            name,
            handler: None,
            inner: HashMap::new(),
        };

        // If the object is a dictionary, then process its items.
        if let Ok(dict) = obj.downcast::<PyDict>() {
            for (key_obj, value) in dict {
                // We expect the key to be a string.
                let key: &str = key_obj.extract()?;
                if key.is_empty() {
                    // An empty key means this node's handler.
                    url.handler = Some(value.into());
                } else {
                    // Parse the child node: if value is a dict, parse recursively;
                    // otherwise, assume it is a leaf handler.
                    let mut child = if value.is_instance(py.get_type::<PyDict>())? {
                        Url::from_pyany(py, value, key.to_string())?
                    } else {
                        Url {
                            name: key.to_string(),
                            handler: Some(value.into()),
                            inner: HashMap::new(),
                        }
                    };

                    // If the key is a parameter (e.g. "<user_id>"), store it in `param`.
                    if is_param(key.to_string()) {
                        if url.inner.contains_key("param") {
                            return Err(PyValueError::new_err(
                                "Multiple parameterized routes at the same level",
                            ));
                        }
                        // Remove the angle brackets for the parameter name.
                        let param_name = key.trim_start_matches('<').trim_end_matches('>').to_string();
                        child.name = param_name;
                        url.inner.insert("param".to_string(), child);
                    } else {
                        // Otherwise, insert it as a static inner route.
                        url.inner.insert(key.to_string(), child);
                    }
                }
            }

            Ok(url)
        } else {
            // If the object is not a dictionary, treat it as a handler for a leaf node.
            url.handler = Some(obj.into());
            Ok(url)
        }
    }

    fn resolve_path(&self, parts: &[&str], index: usize, path_params: &mut HashMap<String, String>) -> Option<(String, Option<Py<PyAny>>)> {
        if index >= parts.len() {
            // If we've reached the end of the path parts, return this node's handler
            return if self.handler.is_some() {
                Some((self.name.clone(), self.handler.clone()))
            } else {
                None
            };
        }

        let current_part = parts[index];
        // First try for an exact match
        if let Some(child) = self.inner.get(current_part) {
            return child.resolve_path(parts, index + 1, path_params);
        }

        // Then try parameter match
        if let Some(param_child) = self.inner.get("param") {
            // Store the parameter value
            path_params.insert(param_child.name.clone(), current_part.to_string());
            return param_child.resolve_path(parts, index + 1, path_params);
        }

        None
    }

    pub fn get(&self, endpoint: String) -> Option<(String, Option<Py<PyAny>>, HashMap<String, String>)> {
        let parts: Vec<&str> = endpoint.split('/').filter(|s| !s.is_empty()).collect();
        // Collect path parameters during resolution
        let mut path_params = HashMap::new();
        if let Some((name, handler)) = self.resolve_path(&parts, 0, &mut path_params) {
            Some((name, handler, path_params))
        } else {
            None
        }
    }
}

// Helper function to determine if a string is a parameter
fn is_param(s: String) -> bool {
    s.starts_with('<') && s.ends_with('>')
}

#[pyfunction]
pub fn get(py: Python, endpoint: String) -> Option<(String, Option<Py<PyAny>>, HashMap<String, String>)> {
    if let Some(url_router) = GLOBAL_ROUTES.get() {
        url_router.get(endpoint)
    } else {
        None
    }
}

// Parse URLs and store in global static
#[pyfunction]
pub fn parse_urls(py: Python, obj: &PyAny) -> PyResult<Url> {
    let parsed = Url::from_pyany(py, obj, "".to_string())?;

    // Store the parsed URLs in the global static
    let _ = GLOBAL_ROUTES.set(parsed.clone());

    Ok(parsed)
}

/// Module definition
#[pymodule]
fn panther_core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Url>()?;
    m.add_function(wrap_pyfunction!(parse_urls, m)?)?;
    m.add_function(wrap_pyfunction!(get, m)?)?;
    Ok(())
}
