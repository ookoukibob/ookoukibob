# Bad Apple contribution-grid GIF

This tool converts a **local video file** into an animated GIF made from
contribution-style squares. It does not draw individual frames by hand and
does not rely on an image-generation service.

## Requirements

```bash
python -m pip install opencv-python-headless pillow
```

## Generate

Put a video file on your computer, then run this from the repository root:

```bash
python tools/bad_apple_contribution.py /path/to/your-video.mp4 \
  --output assets/bad-apple-contribution.gif \
  --fps 8 \
  --palette github
```

For a monochrome Bad Apple look, use `--palette mono`. The default output
grid is 53 columns by 7 rows, matching the proportions of GitHub's activity
graph. The GIF loops forever and is silent.

Useful options:

- `--start 20 --duration 30`: convert a 30-second segment starting at 20s.
- `--fps 6`: reduce the frame rate if the GIF is too large.
- `--palette tokyonight`: use the profile's purple/blue color scheme.
- `--invert`: invert brightness for dark-subject/light-background footage.

## Show it on the profile

After generating the GIF, add this to the root `README.md`:

```html
<div align="center">
  <img src="assets/bad-apple-contribution.gif"
       alt="Bad Apple animated in a GitHub contribution grid"
       width="100%">
</div>
```

Commit both the GIF and README change. GitHub then serves the animation to
everyone who visits the profile; visitors do not need to run JavaScript.

## Media rights

The generator is MIT-style project code, but that does **not** grant rights to
the input video's music or visuals. Supply your own local source file and only
publish the resulting derivative GIF if you have the necessary rights or
permission. The input video is not copied into the repository by this script.
