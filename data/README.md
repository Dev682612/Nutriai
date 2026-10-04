# Dataset

NutriAI uses the [Food-101 dataset](https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/).
`torchvision.datasets.Food101` downloads it automatically when training is run with `--download`.

The first download is large (about 5 GB extracted). Keep the resulting dataset under this directory:

```text
data/
  food-101/
```

For a quick laptop-friendly run, the default configuration trains on ten classes only. The dataset files themselves are ignored by Git.

