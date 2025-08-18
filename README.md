# gcc gcc-11.5.0 (Major v11)

VFX Platform 2025 compatible build package for gcc.

## Package Information

- **Package Name**: gcc
- **Version**: gcc-11.5.0
- **Major Version**: 11
- **Repository**: vfxplatform-2025/gcc-11
- **Description**: VFX Platform 2025 build package

## Build Instructions

```bash
rez-build -i
```

## Package Structure

```
gcc/
├── gcc-11.5.0/
│   ├── package.py      # Rez package configuration
│   ├── rezbuild.py     # Build script
│   ├── get_source.sh   # Source download script (if applicable)
│   └── README.md       # This file
```

## Installation

When built with `install` target, installs to: `/core/Linux/APPZ/packages/gcc/gcc-11.5.0`

## Version Strategy

This repository contains **Major Version 11** of gcc. Different major versions are maintained in separate repositories:

- Major v11: `vfxplatform-2025/gcc-11`

## VFX Platform 2025

This package is part of the VFX Platform 2025 initiative, ensuring compatibility across the VFX industry standard software stack.
