import assert from "node:assert/strict";
import { test } from "node:test";
import { computeDominantFrequency, parseFrameLines } from "./lineParser";

test("parses a single complete line with no remainder", () => {
    const { frames, remainder } = parseFrameLines("", '{"freqBins":[1],"spectrum":[2],"maxMagnitude":3}\n');
    assert.equal(frames.length, 1);
    assert.deepEqual(frames[0], { freqBins: [1], spectrum: [2], maxMagnitude: 3 });
    assert.equal(remainder, "");
});

test("buffers a partial trailing line across chunks", () => {
    const first = parseFrameLines("", '{"freqBins":[1],"spectrum":[2],"maxMagnitude":3}\n{"freqBins":[4]');
    assert.equal(first.frames.length, 1);
    assert.equal(first.remainder, '{"freqBins":[4]');

    const second = parseFrameLines(first.remainder, ',"spectrum":[5],"maxMagnitude":6}\n');
    assert.equal(second.frames.length, 1);
    assert.deepEqual(second.frames[0], { freqBins: [4], spectrum: [5], maxMagnitude: 6 });
});

test("skips malformed lines instead of throwing", () => {
    const { frames } = parseFrameLines("", "not json\n{\"freqBins\":[1],\"spectrum\":[2],\"maxMagnitude\":3}\n");
    assert.equal(frames.length, 1);
});

test("ignores blank lines", () => {
    const { frames } = parseFrameLines("", "\n\n{\"freqBins\":[1],\"spectrum\":[2],\"maxMagnitude\":3}\n\n");
    assert.equal(frames.length, 1);
});

test("computeDominantFrequency picks the bin with the largest magnitude", () => {
    const frame = { freqBins: [100, 200, 300, 400], spectrum: [0.1, 0.9, 0.4, 0.2], maxMagnitude: 0.9 };
    assert.deepEqual(computeDominantFrequency(frame), { frequency: 200, magnitude: 0.9 });
});

test("computeDominantFrequency returns undefined for an empty frame", () => {
    assert.equal(computeDominantFrequency({ freqBins: [], spectrum: [], maxMagnitude: 0 }), undefined);
});

test("computeDominantFrequency returns undefined when freqBins is shorter than spectrum", () => {
    const frame = { freqBins: [100], spectrum: [0.1, 0.9], maxMagnitude: 0.9 };
    assert.equal(computeDominantFrequency(frame), undefined);
});
