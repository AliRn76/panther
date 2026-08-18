//! Link the extension module so CPython resolves its own symbols at import time.
//!
//! `pyo3`'s `extension-module` feature deliberately does not link against
//! libpython: the interpreter that `dlopen`s the module supplies `PyList_New`,
//! `_Py_NoneStruct` and the rest. ELF linkers allow a shared object to carry
//! those undefined symbols, so Linux needs nothing here. Mach-O linkers do not,
//! and a plain `cargo build` on macOS fails with hundreds of "Undefined symbols
//! for architecture arm64" errors unless `dynamic_lookup` is passed explicitly.
//!
//! `maturin` injects this flag itself, so building through it already worked.
//! This exists so a bare `cargo build` or `cargo check` inside `rust/` behaves
//! the same way -- which is what a contributor reaches for first.

fn main() {
    println!("cargo:rerun-if-changed=build.rs");

    // `CARGO_CFG_TARGET_OS` describes the *target*. `cfg!(target_os = "macos")`
    // would describe the host running the build script, and would silently drop
    // the flag when cross-compiling to macOS.
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("macos") {
        println!("cargo:rustc-cdylib-link-arg=-Wl,-undefined,dynamic_lookup");
    }
}
