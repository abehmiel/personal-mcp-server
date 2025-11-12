"""
Utility functions for the MCP server.

This module provides common utilities including Mac MPS detection,
device configuration, and platform-specific optimizations.
"""

import platform
import sys
from enum import Enum
from typing import Any

import torch


class DeviceType(str, Enum):
    """Available compute device types."""

    MPS = "mps"  # Apple Metal Performance Shaders
    CUDA = "cuda"  # NVIDIA CUDA
    CPU = "cpu"  # CPU fallback


class PlatformInfo:
    """Information about the current platform and available compute devices."""

    def __init__(self) -> None:
        """Initialize platform information."""
        self.system = platform.system()
        self.machine = platform.machine()
        self.python_version = sys.version
        self.is_mac = self.system == "Darwin"
        self.is_apple_silicon = self.is_mac and self.machine == "arm64"
        self.is_intel_mac = self.is_mac and self.machine == "x86_64"

    def __repr__(self) -> str:
        """Return string representation of platform info."""
        return (
            f"PlatformInfo(system={self.system}, machine={self.machine}, "
            f"is_mac={self.is_mac}, is_apple_silicon={self.is_apple_silicon})"
        )


def detect_device() -> tuple[str, PlatformInfo]:
    """
    Detect the best available compute device for PyTorch operations.

    This function checks for available compute devices in the following priority:
    1. MPS (Metal Performance Shaders) on Apple Silicon Macs
    2. CUDA on NVIDIA GPUs
    3. CPU as fallback

    Returns:
        tuple[str, PlatformInfo]: A tuple containing:
            - device string suitable for torch.device()
            - PlatformInfo object with platform details

    Examples:
        >>> device, platform_info = detect_device()
        >>> print(f"Using device: {device}")
        Using device: mps
        >>> print(f"Platform: {platform_info.system}")
        Platform: Darwin
    """
    platform_info = PlatformInfo()

    # Check for MPS (Apple Silicon)
    if torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return DeviceType.MPS.value, platform_info

    # Check for CUDA (NVIDIA)
    if torch.cuda.is_available():
        return DeviceType.CUDA.value, platform_info

    # Fallback to CPU
    return DeviceType.CPU.value, platform_info


def get_optimal_device_config() -> dict[str, Any]:
    """
    Get optimal device configuration for the current platform.

    Returns:
        dict[str, Any]: Configuration dictionary with device settings including:
            - device: Device string (mps/cuda/cpu)
            - platform: Platform system name
            - machine: Machine architecture
            - is_apple_silicon: Boolean indicating Apple Silicon
            - recommendations: List of optimization recommendations

    Examples:
        >>> config = get_optimal_device_config()
        >>> print(config['device'])
        mps
        >>> print(config['recommendations'])
        ['Using Metal Performance Shaders for optimal performance']
    """
    device, platform_info = detect_device()

    config: dict[str, Any] = {
        "device": device,
        "platform": platform_info.system,
        "machine": platform_info.machine,
        "is_apple_silicon": platform_info.is_apple_silicon,
        "is_intel_mac": platform_info.is_intel_mac,
        "recommendations": [],
    }

    # Add device-specific recommendations
    if device == DeviceType.MPS.value:
        config["recommendations"].extend(
            [
                "Using Metal Performance Shaders for optimal performance",
                "MPS backend is available and configured",
            ]
        )
    elif device == DeviceType.CUDA.value:
        cuda_device_count = torch.cuda.device_count()
        config["cuda_device_count"] = cuda_device_count
        config["recommendations"].extend(
            [
                "Using NVIDIA CUDA for GPU acceleration",
                f"Available CUDA devices: {cuda_device_count}",
            ]
        )
    else:
        config["recommendations"].extend(
            [
                "Using CPU - consider upgrading to a machine with GPU support",
                "Performance may be limited for large models",
            ]
        )

    return config


def configure_torch_device(device: str | None = None) -> torch.device:
    """
    Configure and return a torch.device object.

    Args:
        device: Optional device string. If None, auto-detects the best device.

    Returns:
        torch.device: Configured PyTorch device object

    Raises:
        ValueError: If the specified device is not available

    Examples:
        >>> device = configure_torch_device()
        >>> print(device)
        mps
        >>> device = configure_torch_device("cpu")
        >>> print(device)
        cpu
    """
    if device is None:
        device, _ = detect_device()

    # Validate device availability
    if device == DeviceType.MPS.value:
        if not (torch.backends.mps.is_available() and torch.backends.mps.is_built()):
            raise ValueError(
                "MPS device requested but not available. "
                "Ensure you're running on an Apple Silicon Mac with MPS support."
            )
    elif device == DeviceType.CUDA.value and not torch.cuda.is_available():
        raise ValueError("CUDA device requested but not available.")

    return torch.device(device)


def get_device_memory_info(device: str | None = None) -> dict[str, Any]:
    """
    Get memory information for the specified device.

    Args:
        device: Device string (mps/cuda/cpu). If None, uses auto-detected device.

    Returns:
        dict[str, Any]: Dictionary containing memory information

    Examples:
        >>> info = get_device_memory_info()
        >>> print(info['device'])
        mps
    """
    if device is None:
        device, _ = detect_device()

    info: dict[str, Any] = {"device": device}

    if device == DeviceType.CUDA.value and torch.cuda.is_available():
        info["total_memory"] = torch.cuda.get_device_properties(0).total_memory
        info["allocated_memory"] = torch.cuda.memory_allocated(0)
        info["cached_memory"] = torch.cuda.memory_reserved(0)
    elif device == DeviceType.MPS.value:
        # MPS doesn't provide detailed memory info through PyTorch
        info["note"] = "MPS memory info not available through PyTorch"
    else:
        info["note"] = "Memory info only available for CUDA devices"

    return info
