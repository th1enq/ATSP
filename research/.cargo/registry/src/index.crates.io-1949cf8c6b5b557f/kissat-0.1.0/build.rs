extern crate cc;

use std::fs;

pub fn main() {
    let excluded = [
        "application.c",
        "build.c",
        "handle.c",
        "main.c",
        "parse.c",
        "witness.c",
    ];
    let files = fs::read_dir("kissat/src")
        .expect("Cannot find 'kissat' directory")
        .filter_map(Result::ok)
        .filter(|p| {
            let name = p.file_name().to_string_lossy().into_owned();
            name.ends_with(".c") && !excluded.contains(&name.as_str())
        })
        .map(|p| p.path())
        .collect::<Vec<_>>();

    cc::Build::new()
        .define("COMPACT", None)
        .define("NDEBUG", None)
        .define("NOPTIONS", None)
        .define("NPROOFS", None)
        .define("QUIET", None)
        .files(files)
        .compile("kissat");
}
