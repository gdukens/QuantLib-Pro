#  Gaussian Cookbook

[![PyPI version](https://badge.fury.io/py/gaussian-cookbook.svg)](https://badge.fury.io/py/gaussian-cookbook)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Build](https://img.shields.io/github/actions/workflow/status/yourusername/gaussian-cookbook/python-package.yml)](https://github.com/yourusername/gaussian-cookbook/actions)

> A high-precision simulation library for **Gaussian stochastic processes**, with a notebook-style cookbook of ready-to-use **recipes** for research, teaching, and experimentation.

---

##  Features

-  **Continuous and Discrete-Time** stochastic processes
-  Rich library of **discretizations and numerical solvers**
-  Interactive **Jupyter Notebook Recipes**
-  Includes:
  - **Brownian Motion**
  - **Brownian Bridge**
  - **Fractional Brownian Motion (fBM)**
-  Easily extendable to new Gaussian processes

---

##  Installation

```bash
pip install gaussian-cookbook

---

##  Features

-  **Continuous and Discrete-Time** stochastic processes
-  Rich library of **discretizations and numerical solvers**
-  Interactive **Jupyter Notebook Recipes**
-  Includes:
  - **Brownian Motion**
  - **Brownian Bridge**
  - **Fractional Brownian Motion (fBM)**
-  Easily extendable to new Gaussian processes

---

##  Installation

```bash
pip install gaussian-cookbook
````

Or install the development version:

```bash
git clone https://github.com/RomanMichaelPaolucci/gaussian-cookbook.git
cd gaussian-cookbook
pip install -e .
```

---

##  Recipe Notebooks

We provide **hands-on, annotated notebooks** that walk through the theory and simulation techniques for each process.

| Process                    | Continuous Time | Discrete Time | Notebooks                              |
| -------------------------- | --------------- | ------------- | -------------------------------------- |
| Brownian Motion            |                |              | [View](notebooks/BrownianMotion.ipynb) |
| Brownian Bridge            |                |              | [View](notebooks/BrownianBridge.ipynb) |
| Fractional Brownian Motion |                |              | [View](notebooks/FractionalBM.ipynb)   |

> Recipes use NumPy, SciPy, and Matplotlib for simulation and visualization. Each recipe is self-contained and suitable for learning, experimentation, and benchmarking.

---

##  Use Cases

*  Teaching stochastic processes
*  Financial modeling & Monte Carlo simulations
*  Neuroscience and signal modeling
*  Research in physics, mathematics, and statistics
*  Customizable for new kernels and process models

---

##  Example Usage

```python
from gaussian_cookbook.processes import BrownianMotion

bm = BrownianMotion(t_max=1.0, n_steps=500)
path = bm.sample()

bm.plot(path)
```

---

##  Documentation

* [ API Reference](https://yourusername.github.io/gaussian-cookbook/)
* [ Recipe Gallery](notebooks/)
* [ How to Add a New Process](docs/how_to_add_new_process.md)

---

##  Roadmap

* [ ] Multi-dimensional processes
* [ ] Gaussian Process Regression examples
* [ ] Interactive Bokeh/Plotly visualizations
* [ ] Extended fBM models (e.g., Hosking, Davies–Harte)
* [ ] PyTorch/NumPyro integration for stochastic modeling

---

##  Contributing

We welcome contributions! Whether it's fixing a bug, adding a new stochastic process, or improving the docs:

1. Fork the repo
2. Create a feature branch
3. Submit a pull request 

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

##  Why "Cookbook"?

This project is inspired by the philosophy of **learning by example**. Like a culinary cookbook, we offer **ready-to-serve "recipes"**—not just raw ingredients (code)—so you can dive in, explore, and build your own models with ease.

---

##  License

Licensed under the MIT License. See [`LICENSE`](LICENSE) for more details.

---

##  Stay Connected

*  Academic? Cite us: Coming soon!
*  Found it useful? Star ⭐ the repo and share!
*  Issues or questions? Open a GitHub Issue or join the [discussions](https://github.com/yourusername/gaussian-cookbook/discussions).

---

> *Gaussian Cookbook* — your essential toolkit for simulating, visualizing, and understanding stochastic processes.

```

---

Let me know if you'd like me to tailor this further (e.g. add logo, citations, links to published papers, Binder/Colab integration, etc.).
```
