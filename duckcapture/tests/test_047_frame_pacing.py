"""Regression checks: no 90 Hz -> 45 FPS aliasing; preserve 0.4.6 queue."""
import pytest
from duckcapture.frame_pacer import SourceFramePacer

@pytest.mark.parametrize('input_fps', [60, 75, 90, 100, 120, 144, 165, 240])
def test_realistic_capture_rates_preserve_60_unique_fps(input_fps):
    pacer = SourceFramePacer(60)
    duration = 12
    times = [i / input_fps for i in range(input_fps * duration)]
    accepted = [t for t in times if pacer.allow(t)]
    assert 59.4 <= len(accepted) / duration <= 60.15, (input_fps, len(accepted))
    assert len(accepted) == pacer.accepted

@pytest.mark.parametrize('input_fps', [25, 30, 40, 45, 50])
def test_slow_source_not_mistaken_for_60_fps(input_fps):
    pacer = SourceFramePacer(60)
    count = sum(pacer.allow(i / input_fps) for i in range(input_fps * 3))
    assert count == 3 * input_fps

@pytest.mark.parametrize('source,target', [(90, 60), (144, 120), (75, 45), (120, 30), (240, 120)])
def test_pacer_tracks_other_requested_fps(source, target):
    pacer = SourceFramePacer(target)
    count = sum(pacer.allow(i/source) for i in range(source * 10))
    assert abs(count/10-target) < 1

def test_long_pause_resets_phase_without_burst():
    pacer = SourceFramePacer(60)
    assert pacer.allow(100)
    assert not pacer.allow(100.001)
    assert pacer.allow(101)
    assert pacer.next_due == pytest.approx(101 + 1/60)
    assert not pacer.allow(101.001)

@pytest.mark.parametrize('target', [0, -1, float('nan'), float('inf')])
def test_invalid_target_rejected(target):
    with pytest.raises(ValueError):
        SourceFramePacer(target)

def test_90hz_old_fixed_gap_yielded_only_45_per_second():
    # Mathematical regression for the previous bug (90Hz input, 60Hz target).
    times = [i / 90 for i in range(90 * 10)]
    prev = -1
    old_count = 0
    for t in times:
        if t - prev < 0.96 / 60:
            continue
        prev = t
        old_count += 1
    new_pacer = SourceFramePacer(60)
    new_count = sum(new_pacer.allow(t) for t in times)
    assert 44 <= old_count/10 <= 46
    assert 59 <= new_count/10 <= 61
