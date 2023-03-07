# Stamp Classifier Step

## Description

Process alert stream using the selected stamp classifier, either for 
[ZTF](https://github.com/alercebroker/stamp_classifier) or 
[ATLAS](https://github.com/alercebroker/atlas_stamp_classifier).

Since only the first alert for a given object has to be classified, the step checks
the database for the object and if it has been classified already, these objects will be removed
from the messages and not classified. To ensure if the classification already exists, it will only 
check for the classifier name, i.e., even if the step is using a different version, it will
not classify new alerts for the same object. On the other hand, since the classifier names differ,
the first alert from ZTF will be added to the classifications *and* the first ATLAS alert as well
if the given object has alerts from both surveys.

In case the same object has more than one alert in the same message processing batch, only the earliest
alert will be classified. This is based on the `mjd` field of the alert. It is perfectly normal for the
step to classify fewer alerts than it consumes based on the previous two restrictions.

#### Previous steps:
- [Sorting Hat](https://github.com/alercebroker/sorting_hat_step)

#### Next steps:
- None

## IMPORTANT NOTE ABOUT VERSIONS

Requires Python 3.7.

Due to the different versions of tensorflow used by each classifier, it is not possible to run both on
the same environment:

- ZTF: The classifier has to be included as a [zip file](https://github.com/alercebroker/stamp_classifier/releases/download/1.0.0/model.zip) (uses tensorflow 1) 
- ATLAS: The classifier is installed using pip as part of the requirements (uses tensorflow 2)

Due to it being in the requirements, the ATLAS classifier is installed even when intending to create
the step for the ZTF stream. This won't result in version conflicts **as long as the requirements in
the ATLAS classifier do not have fixed versions**. However, it won't be possible to run the ATLAS stamp classifier
in an environment set for the ZTF environment.

## Environment variables

These are required only when running through the scripts, as is the case for the Docker images.

### Consumer setup

- `CONSUMER_TOPICS`: Some topics. String separated by commas, e.g., `topic_one` or `topic_two,topic_three`
- `CONSUMER_SERVER`: Kafka host with port, e.g., `localhost:9092`
- `CONSUMER_GROUP_ID`: Name for consumer group, e.g., `correction`
- `CONSUME_TIMEOUT`: (optional) Timeout for consumer
- `CONSUME_MESSAGES`: (optional) Number of messages consumed in a batch

### Output producer setup

- `PRODUCER_TOPIC_FORMAT`: 
- `PRODUCER_SERVER`: Kafka host with port, e.g., `localhost:9092`
- `PRODUCER_CHANGE_HOUR`: 
- `PRODUCER_RETENTION_DAYS`:
- `PRODUCER_SASL_USERNAME`:
- `PRODUCER_SASL_PASSWORD`:

### Scribe producer setup

The [scribe](https://github.com/alercebroker/alerce-scribe) will write results in the database. 

- `SCRIBE_TOPIC`: Topic name, e.g., `topic_one`
- `SCRIBE_SERVER`: Kafka host with port, e.g., `localhost:9092`

### Metrics producer setup

- `METRICS_TOPIC`: Topic name, e.g., `topic_one`
- `METRICS_SERVER`: Kafka host with port, e.g., `localhost:9092`

### Classifier setup

- `CLASSIFIER_STRATEGY`: Which classifier to use. Either `ZTF` or `ATLAS`
- `MODEL_NAME`: Model name for metadata, e.g., `ztf_stamp_classifier`
- `MODEL_VERSION`: Model version for metadata, e.g., `1.0.0`

### Database setup

- `MONGODB_SECRET_NAME`: Name for the MongoDB secret inside AWS


## Run the released image

For each release **two** images are uploaded to GitHub packages, one for each classifier. To download both:

```bash
docker pull ghcr.io/alercebroker/ztf_stamp_classifier_step:latest
docker pull ghcr.io/alercebroker/atlas_stamp_classifier_step:latest
```
## Local Installation

### Downloading and installing ZTF model (only for ZTF)

We are using the [zipped model](https://github.com/alercebroker/stamp_classifier/releases/download/1.0.0/model.zip) 
from the release.

A ZTF classifier step expects the model inside the `model` folder, at the base of the repository.
```bash
unzip model.zip -d model
```

Then we need to install the model's required packages.
```bash
pip install -r model/requirements.txt
```

### Requirements (all)

To install the repository specific packages run:
```bash
pip install -r requirements.txt
```
