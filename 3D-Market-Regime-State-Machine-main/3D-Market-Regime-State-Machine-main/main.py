from regime_model import RegimeModel
from visualization import visualize_regimes

def main():
    model = RegimeModel('SPY')
    model.process()
    visualize_regimes(model)

if __name__ == '__main__':
    main()
