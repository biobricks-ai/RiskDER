import os
import pickle
import hashlib
import functools

class SimpleCache:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, func_name, args, kwargs):
        """Generate a unique cache file path based on function name and arguments."""
        key = f"{func_name}_{hashlib.md5(pickle.dumps((args, kwargs))).hexdigest()}.pkl"
        return os.path.join(self.cache_dir, key)

    def cache(self, func):
        """Decorator that caches function output to a file."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_path = self._get_cache_path(func.__name__, args, kwargs)
            if os.path.exists(cache_path):
                with open(cache_path, "rb") as f:
                    return pickle.load(f)

            result = func(*args, **kwargs)
            with open(cache_path, "wb") as f:
                pickle.dump(result, f)
            return result

        return wrapper

# Usage example
cache = SimpleCache(cache_dir="cache")

@cache.cache
def expensive_function(x, y):
    print("Computing...")
    return x * y

if __name__ == "__main__":
    print(expensive_function(2, 3))  # First call computes and caches
    print(expensive_function(2, 3))  # Second call loads from cache
