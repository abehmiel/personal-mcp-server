"""Tests for utility functions."""

import pytest
import torch

from rag_server.utils import (
    DeviceType,
    PlatformInfo,
    configure_torch_device,
    detect_device,
    get_device_memory_info,
    get_optimal_device_config,
)


class TestPlatformInfo:
    """Tests for PlatformInfo class."""

    def test_platform_info_initialization(self) -> None:
        """Test that PlatformInfo initializes correctly."""
        platform_info = PlatformInfo()
        assert platform_info.system in ["Darwin", "Linux", "Windows"]
        assert platform_info.machine in ["x86_64", "arm64", "AMD64", "aarch64"]
        assert isinstance(platform_info.is_mac, bool)
        assert isinstance(platform_info.is_apple_silicon, bool)

    def test_platform_info_repr(self) -> None:
        """Test string representation of PlatformInfo."""
        platform_info = PlatformInfo()
        repr_str = repr(platform_info)
        assert "PlatformInfo" in repr_str
        assert "system=" in repr_str
        assert "machine=" in repr_str


class TestDeviceDetection:
    """Tests for device detection functions."""

    def test_detect_device_returns_valid_device(self) -> None:
        """Test that detect_device returns a valid device type."""
        device, platform_info = detect_device()
        assert device in [DeviceType.MPS.value, DeviceType.CUDA.value, DeviceType.CPU.value]
        assert isinstance(platform_info, PlatformInfo)

    def test_device_type_enum(self) -> None:
        """Test DeviceType enum values."""
        assert DeviceType.MPS.value == "mps"
        assert DeviceType.CUDA.value == "cuda"
        assert DeviceType.CPU.value == "cpu"

    def test_get_optimal_device_config(self) -> None:
        """Test optimal device configuration retrieval."""
        config = get_optimal_device_config()
        assert "device" in config
        assert "platform" in config
        assert "machine" in config
        assert "is_apple_silicon" in config
        assert "recommendations" in config
        assert isinstance(config["recommendations"], list)
        assert len(config["recommendations"]) > 0

    def test_configure_torch_device_auto_detect(self) -> None:
        """Test automatic device configuration."""
        device = configure_torch_device()
        assert isinstance(device, torch.device)
        assert str(device) in ["mps", "cuda", "cpu"]

    def test_configure_torch_device_cpu(self) -> None:
        """Test explicit CPU device configuration."""
        device = configure_torch_device("cpu")
        assert isinstance(device, torch.device)
        assert str(device) == "cpu"

    @pytest.mark.skipif(
        not (torch.backends.mps.is_available() and torch.backends.mps.is_built()),
        reason="MPS not available",
    )
    def test_configure_torch_device_mps(self) -> None:
        """Test MPS device configuration when available."""
        device = configure_torch_device("mps")
        assert isinstance(device, torch.device)
        assert str(device) == "mps"

    def test_configure_torch_device_invalid_raises_error(self) -> None:
        """Test that invalid device raises appropriate error."""
        # Try to configure MPS on non-Mac systems
        if not (torch.backends.mps.is_available() and torch.backends.mps.is_built()):
            with pytest.raises(ValueError, match="MPS device requested but not available"):
                configure_torch_device("mps")

    def test_get_device_memory_info(self) -> None:
        """Test device memory information retrieval."""
        info = get_device_memory_info()
        assert "device" in info
        assert info["device"] in ["mps", "cuda", "cpu"]

    def test_get_device_memory_info_cpu(self) -> None:
        """Test CPU device memory info."""
        info = get_device_memory_info("cpu")
        assert info["device"] == "cpu"
        assert "note" in info
