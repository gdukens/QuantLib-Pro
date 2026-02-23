import numpy as np

class VolatilityShockwaveSimulator:
    def __init__(self, S0, mu, sigma_low, sigma_high, T, dt, switch_prob, shock_prob, shock_magnitude):
        self.S0 = S0
        self.mu = mu
        self.sigma_low = sigma_low
        self.sigma_high = sigma_high
        self.T = T
        self.dt = dt
        self.switch_prob = switch_prob
        self.shock_prob = shock_prob
        self.shock_magnitude = shock_magnitude
        self.reset()

    def reset(self):
        self.time = np.arange(0, self.T, self.dt)
        self.prices = [self.S0]
        self.volatility = [self.sigma_low]
        self.shockwaves = [False]
        self.current_sigma = self.sigma_low

    def step(self):
        last_price = self.prices[-1]
        # Volatility regime switch
        if np.random.rand() < self.switch_prob:
            self.current_sigma = self.sigma_high if self.current_sigma == self.sigma_low else self.sigma_low
        # Shockwave event
        shock = False
        if np.random.rand() < self.shock_prob:
            self.current_sigma *= self.shock_magnitude
            shock = True
        # Geometric Brownian Motion
        dW = np.random.normal(0, np.sqrt(self.dt))
        new_price = last_price * np.exp((self.mu - 0.5 * self.current_sigma ** 2) * self.dt + self.current_sigma * dW)
        self.prices.append(new_price)
        self.volatility.append(self.current_sigma)
        self.shockwaves.append(shock)
        # Reset shockwave after one step
        if shock:
            self.current_sigma /= self.shock_magnitude

    def run(self):
        self.reset()
        for _ in self.time[1:]:
            self.step()
        return np.array(self.prices), np.array(self.volatility), np.array(self.shockwaves)
