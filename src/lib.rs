use std::collections::HashMap;
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
    fn from_pyany(py: Python, obj: &PyAny, name: String) -> PyResult<Self> {
        let mut url = Url {
            name,
            handler: None,
            inner: HashMap::new(),
        };

        if let Ok(dict) = obj.downcast::<PyDict>() {
            for (key_obj, value) in dict {
                let key: &str = key_obj.extract()?;
                if key.is_empty() {
                    url.handler = Some(value.into());
                } else {
                    let mut child = if value.is_instance(py.get_type::<PyDict>())? {
                        Url::from_pyany(py, value, key.to_string())?
                    } else {
                        Url {
                            name: key.to_string(),
                            handler: Some(value.into()),
                            inner: HashMap::new(),
                        }
                    };

                    if is_param(key.to_string()) {
                        if url.inner.contains_key("param") {
                            return Err(PyValueError::new_err(
                                "Multiple parameterized routes at the same level",
                            ));
                        }
                        let param_name = key.trim_start_matches('<').trim_end_matches('>').to_string();
                        child.name = param_name;
                        url.inner.insert("param".to_string(), child);
                    } else {
                        url.inner.insert(key.to_string(), child);
                    }
                }
            }

            Ok(url)
        } else {
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

fn is_param(s: String) -> bool {
    s.starts_with('<') && s.ends_with('>')
}

#[pyfunction]
pub fn get(_py: Python, endpoint: String) -> Option<(String, Option<Py<PyAny>>, HashMap<String, String>)> {
    if let Some(url_router) = GLOBAL_ROUTES.get() {
        url_router.get(endpoint)
    } else {
        None
    }
}

#[pyfunction]
pub fn parse_urls(py: Python, obj: &PyAny) -> PyResult<Url> {
    let parsed = Url::from_pyany(py, obj, "".to_string())?;
    let _ = GLOBAL_ROUTES.set(parsed.clone());

    Ok(parsed)
}

/// Module definition
#[pymodule]
fn panther_core(_py: Python, m: &PyModule) -> PyResult<()> {
    // m.add_class::<Url>()?;
    m.add_function(wrap_pyfunction!(parse_urls, m)?)?;
    m.add_function(wrap_pyfunction!(get, m)?)?;
    Ok(())
}
