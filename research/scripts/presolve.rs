#[path = "../vendor/uzl/src/presolve.rs"]
mod presolve;
use std::io::{self, BufRead};
fn main() {
    let mut n = 0;
    let mut edges = Vec::new();
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let t: Vec<_> = line.split_whitespace().collect();
        if t.is_empty() || t[0] == "c" {continue;}
        if t[0] == "p" {n = t[2].parse().unwrap();continue;}
        let mut e: Vec<usize> = t.iter().map(|s| s.parse().unwrap()).collect();
        e.sort();e.dedup();edges.push(e);
    }
    let mut p = presolve::Presolve::from_edge_list(n, &edges);
    p.apply(None);
    eprintln!("picks {:?}", p.get_picks());
    let remaining = p.get_remaining_edges();
    let mut used = vec![false;n+1];
    for e in &remaining {for &v in e {used[v]=true;}}
    let mut map=vec![0;n+1];let mut inv=Vec::new();
    for v in 1..=n {if used[v] {inv.push(v);map[v]=inv.len();}}
    eprintln!("mapping {:?}",inv);
    println!("p hs {} {}",inv.len(),remaining.len());
    for e in remaining {println!("{}",e.iter().map(|&v| map[v].to_string()).collect::<Vec<_>>().join(" "));}
}
