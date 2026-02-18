"""Sample code with missing documentation for testing."""


def process_data(data, options, callback):
    items = []
    for item in data:
        if item.get("active"):
            transformed = transform_item(item, options)
            if transformed:
                items.append(transformed)
    return callback(items)


def transform_item(item, options):
    result = {}
    for key, value in item.items():
        if key in options.get("include", []):
            if options.get("uppercase"):
                result[key.upper()] = value
            else:
                result[key] = value
    return result if result else None


class DataProcessor:
    def __init__(self, config, logger, cache):
        self.config = config
        self.logger = logger
        self.cache = cache
        self._initialized = False

    def initialize(self):
        self._initialized = True
        return self

    def process(self, input_data):
        if not self._initialized:
            raise RuntimeError("Not initialized")

        results = []
        for record in input_data:
            processed = self._process_record(record)
            if processed:
                results.append(processed)
        return results

    def _process_record(self, record):
        if not record.get("id"):
            return None

        cached = self.cache.get(record["id"])
        if cached:
            return cached

        result = {
            "id": record["id"],
            "processed": True,
            "data": record.get("data", {}),
        }

        self.cache.set(record["id"], result)
        return result

    def cleanup(self):
        self.cache.clear()
        self._initialized = False


def calculate_metrics(values, weights, normalize=False):
    if not values:
        return 0

    total = 0
    weight_sum = 0

    for i, value in enumerate(values):
        weight = weights[i] if i < len(weights) else 1
        total += value * weight
        weight_sum += weight

    result = total / weight_sum if weight_sum else 0

    if normalize:
        max_val = max(values) if values else 1
        result = result / max_val

    return result


async def fetch_and_process(urls, processor, max_concurrent=5):
    import asyncio

    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(url):
        async with semaphore:
            response = await http_client.get(url)
            return processor(response.json())

    tasks = [fetch_one(url) for url in urls]
    return await asyncio.gather(*tasks)
