use std::fs;
use std::process::{Command, ExitCode};

fn run() -> Result<(), String> {
    let listing = Command::new("scanimage")
        .arg("-L")
        .output()
        .map_err(|error| format!("Could not start scanimage: {error}"))?;
    let listing_text = String::from_utf8_lossy(&listing.stdout);
    let device = listing_text
        .lines()
        .find_map(|line| {
            let start = line.find("device `")? + "device `".len();
            let remainder = &line[start..];
            let end = remainder.find("' is a")?;
            Some(&remainder[..end])
        })
        .ok_or_else(|| "No SANE scanner found. Check scanimage -L and USB access.".to_string())?;

    fs::create_dir_all("scans").map_err(|error| format!("Could not create scans/: {error}"))?;
    let result = Command::new("scanimage")
        .args([
            "--device-name",
            device,
            "--format=png",
            "--output-file=scans/scanned.png",
        ])
        .status()
        .map_err(|error| format!("Could not start scanimage: {error}"))?;

    if !result.success() {
        return Err("The scanner failed to complete the scan.".to_string());
    }
    println!("Saved scan to scans/scanned.png");
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("{error}");
            ExitCode::FAILURE
        }
    }
}