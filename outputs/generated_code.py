import numpy as np

class DataAnalyzer:
    def __init__(self, **kwargs):
        self.data = np.array(kwargs['data'])
        if self.data.ndim != 2 or self.data.shape[1] != 5:
            raise ValueError("Input array must have shape (n,5)")

    def calculate_statistics(self, **kwargs):
        results = {}
        for col in [0, 2]:
            col_data = self.data[:, col]
            results[f'column_{col+1}'] = {
                'mean': np.mean(col_data),
                'variance': np.var(col_data, ddof=1)
            }
        return results

def main():
    example_data = [
        [1.2, 2.3, 3.4, 4.5, 5.6],
        [6.7, 7.8, 8.9, 9.1, 10.2],
        [11.3, 12.4, 13.5, 14.6, 15.7]
    ]
    
    analyzer = DataAnalyzer(data=example_data)
    stats = analyzer.calculate_statistics()
    
    for col, values in stats.items():
        print(f"{col}:")
        print(f"  Mean: {values['mean']:.4f}")
        print(f"  Variance: {values['variance']:.4f}\n")

if __name__ == "__main__":
    main()