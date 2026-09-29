package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func scannerDevice() (string, error) {
	output, err := exec.Command("scanimage", "-L").CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("could not list SANE scanners: %w: %s", err, strings.TrimSpace(string(output)))
	}

	for _, line := range strings.Split(string(output), "\n") {
		start := strings.Index(line, "device `")
		if start < 0 {
			continue
		}
		deviceStart := start + len("device `")
		end := strings.Index(line[deviceStart:], "' is a")
		if end >= 0 {
			return line[deviceStart : deviceStart+end], nil
		}
	}
	return "", fmt.Errorf("no SANE scanner found; check scanimage -L and USB access")
}

func main() {
	device, err := scannerDevice()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := os.MkdirAll("scans", 0755); err != nil {
		fmt.Fprintln(os.Stderr, "could not create scans directory:", err)
		os.Exit(1)
	}

	command := exec.Command("scanimage", "--device-name", device, "--format=png", "--output-file="+filepath.Join("scans", "scanned.png"))
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr
	if err := command.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "scanner failed:", err)
		os.Exit(1)
	}
	fmt.Println("Saved scan to scans/scanned.png")
}
