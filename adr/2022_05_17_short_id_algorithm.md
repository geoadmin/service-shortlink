# Continuous integration platform

> `Status: proposed`
>
> `Date: 2022-05-17`
>
> `Author: Brice Schaffner`

## Context

The actual short ID algorithm for `service-shortlink` uses a kind of counter based on the computer time. 
Its takes the actual timestamp rounded to the milliseconds (millisecond timestamp from 1970.01.01 00:00:00.000), to 
reduce the size of this timestamp, `1'000'000'000'000` is substracted from it, which give us the number
of milliseconds from `2001.09.09 03:46:40.000`.

### PROS of actual algorithm

- Very simple
- With a request rate less than `1 rps` (current rate is `~0.3 rps`) collision  are quite unlikely and can be easily avoided with very small number of retries.

### CONS of actual algorithm

- Size of short ID is dynamic, current is 10 characters but will increase in near future. Around `2037.01.01` we will have 11 characters.

## Nano ID - random short ID

We could reduced the size of the ID to 8 characters by using [Nano ID](https://github.com/ai/nanoid). 
Here however we have an issue with collision ! Based on [Nano ID collision calculator](https://zelark.github.io/nano-id-cc/)
and our current request rate of ~1050 rph (request per hour), we will have a 1% collision risk in 99 days ! 
Now looking closer to the mathematics (note I might be wrong here as I'm not a mathematician) we can 
compute the collision probability as follow:

- d := number of different possible IDs (see [Permutation with Replacement](https://www.calculatorsoup.com/calculators/discretemathematics/permutationsreplacement.php))
- n := number of IDs
- `1-((d-1)/d**(n*-1)/2)` [Birthday Paradox / Probability of a shared birthday (collision)](https://en.wikipedia.org/wiki/Birthday_problem)

```python
d = 64**8
print(f"{d:,}")                                                                                                 
281,474,976,710,656

# Number of IDs after 100 days
n = 1050 * 24 * 100

collision = 1-((d-1)/d)**(n*(n-1)/2)
print(str(int(collision * 100)) + '%')
1%

# Number of IDs after 1 years
n = 1050 * 24 * 365 * 1

collision = 1-((d-1)/d)**(n*(n-1)/2)
print(str(int(collision * 100)) + '%')
13%

# Number of IDs after 3 years
n = 1050 * 24 * 365 * 3

collision = 1-((d-1)/d)**(n*(n-1)/2)
print(str(int(collision * 100)) + '%')
74%

# Number of IDs after 5 years
n = 1050 * 24 * 365 * 5

collision = 1-((d-1)/d)**(n*(n-1)/2)
print(str(int(collision * 100)) + '%')
97%

# Number of IDs after 10 years
n = 1050 * 24 * 365 * 10

collision = 1-((d-1)/d)**(n*(n-1)/2)
print(str(int(collision * 100)) + '%')
99%
```

### Nano ID tests

I tested Nano ID with 1 and 2 characters with the following code

```python
# app/helpers/utils.py
def generate_short_id():
    return generate(size=8)

# tests/unit_tests/test_helpers.py
class TestDynamoDb(BaseShortlinkTestCase):
    @params(1, 2)
    @patch('app.helpers.dynamo_db.generate_short_id')
    def test_duplicate_short_id_end_of_ids(self, m, mock_generate_short_id):
        regex = re.compile(r'^[0-9a-zA-Z-_]{' + str(m) + '}$')

        def generate_short_id_mocker():
            return generate(size=m)

        mock_generate_short_id.side_effect = generate_short_id_mocker
        # with generate(size=1) we have 64 different possible IDs, as we get closer to this number
        # the collision will increase. Here we make sure that we can generate at least the half
        # of the maximal number of unique ID with less than the max retry.
        n = 64
        max_ids = int(factorial(n) / (factorial(m) * factorial(n - m)))
        logger.debug('Try to generate %d entries', max_ids)
        for i in range(max_ids):
            logger.debug('-' * 80)
            logger.debug('Add entry %d', i)
            if i < max_ids / 2:

                next_entry = add_url_to_table(
                    f'https://www.example/test-duplicate-id-end-of-ids-{i}-url'
                )
                self.assertIsNotNone(
                    regex.match(next_entry['shortlink_id']),
                    msg=f"short ID {next_entry['shortlink_id']} don't match regex"
                )
            else:
                # more thant the half of max ids might fail due to more than COLLISION_MAX_RETRY
                # retries, therefore ignore those errors
                try:
                    next_entry = add_url_to_table(
                        f'https://www.example/test-duplicate-id-end-of-ids-{i}-url'
                    )
                except db_table.meta.client.exceptions.ConditionalCheckFailedException:
                    pass
        # Make sure that generating a 65 ID fails.
        with self.assertRaises(db_table.meta.client.exceptions.ConditionalCheckFailedException):
            add_url_to_table('https://www.example/test-duplicate-id-end-of-ids-65-url')

```

The test with 1 character passed but with 2 not ! This means that with 1 character we could generate
up to half of the available IDs without having more than 10 retries. While with 2 character we could not ! 
To note also that the formula used here to compute the maximal number of IDs was wrong and generated less
IDs than the correct formula `max_ids = n**m`:

- `max_ids = n**m`
  - `max_ids = 64**1 = 64`
  - `max_ids = 64**2 = 4096`
- `int(factorial(n) / (factorial(m) * factorial(n - m)))`
  - `n = 64; m = 1; int(factorial(n) / (factorial(m) * factorial(n - m))) = 64`
  - `n = 64; m = 2; int(factorial(n) / (factorial(m) * factorial(n - m))) = 2016`

### Nano ID conclusion

Based on the formula and computation above we have a high risk to have too many collision already
after 3 years ! So this algorithm cannot be used with 8 characters.

## Other algorithms

After some research on shortlink algorithm, I found out that there are two category of algorithms:

1. Random ID generator (e.g. NanoID)
2. Counter

While the first is very easy to implement, the size of the ID highly depends on the generation rates and
max life of the IDs. For our use case we have a quite high generation rate and an infinite life of the IDs.
This means that it is not the best algorithm.

However the second algorithm is more robust for our use case. Starting a counter from 0 we could reduce the ID significantly (less than 6 characters). However it would require to change the backend to have an atomic counter. With our current
current implementation (k8s with DynamoDB) this is not feasible. So we would need to change the DB (maybe PSQL?) 
and rewrite the whole python service.

## Decision (to be accepted by others)

I think with the current algorithm which we used the past years, we are good up to 2037 where we will have one more character.
This algo is quite robust, not the more effective in terms of ID length but very simple and fast.

Changing to a Random ID generator includes based on our generation rate and life cycle, is way too risky and brittle.

Changing to a real counter approach would require a lot of effort, starting from scratch.

So IMHO sticking to the current algorithm is the best for the moment. In future we can reduce the size of
the shortlink by reducing the size of the host name wich is quite long; e.g. `s.bgdi.ch` instead of `s.geo.admin.ch`.
