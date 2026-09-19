import numpy as np

from Audio_SpectraCLI.headless import downsample_max_pool, parse_args


def test_downsample_returns_input_unchanged_when_already_short():
    values = np.array([1.0, 2.0, 3.0])
    result = downsample_max_pool(values, 5)
    assert list(result) == [1.0, 2.0, 3.0]


def test_downsample_max_pools_into_requested_bar_count():
    values = np.arange(10, dtype=float)
    result = downsample_max_pool(values, 3)
    assert len(result) == 3
    assert result[-1] == 9  # last group's max is the final value


def test_parse_args_defaults():
    args = parse_args([])
    assert args.fs == 44100
    assert args.block_size == 4096
    assert args.bars == 64
    assert args.noise_threshold == 0.05


def test_parse_args_overrides():
    args = parse_args(["--fs", "22050", "--bars", "32"])
    assert args.fs == 22050
    assert args.bars == 32
