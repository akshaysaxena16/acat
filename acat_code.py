# import all required libraries
import tensorflow as tf
import pandas as pd
#import tensorflow as tf
#import pandas as pd
#import tensorflow as tf
import numpy as np
import tempfile
import collections
from sklearn.cross_validation import train_test_split
from sklearn.metrics import accuracy_score
headers = ['business_classification', 'business_impact', 'business_relevance',
       'category_id', 'data_confidentiality', 'eoldriver', 'extensibility',
       'geographical_scope', 'has_dependencies', 'id', 'io_intensity',
       'latency_sensitivity', 'no_of_users', 'scalability', 'service_level',
       'source_code_available', 'stage', 'type', 'user_facing',
       'workload_variation', 'dependencies.Hardware.Dependent',
       'dependencies.Operating.Environment.Dependent',
       'dependencies.Operating.System.Dependent', 'IsPassPlatAvail',
       'IsHarwareSupported', 'IsOSSupported', 'IsPlatformSupported',
       'IsDatabaseSupported']

#read csv
ds = pd.read_csv('completeData.csv', usecols = headers)

categories={}
for f in headers:
    ds[f] = ds[f].astype('category')
    categories[f] = ds[f].cat.categories




labels = pd.read_csv('completeData.csv', usecols = ['pivot.disposition_1'])
#print(labels)
#covert strings into numericals
df = pd.get_dummies(ds, columns = headers)
#print(df)
df_num, df_labels = pd.factorize(labels['pivot.disposition_1'])
print(df_num)
#print(df_num)
stack = pd.DataFrame(np.column_stack((df_num, df)))
#split data
df_train, df_test = train_test_split(stack, test_size=0.25)

num_train_entries = df_train.shape[0]
num_train_features = df_train.shape[1]-1

num_test_entries = df_test.shape[0]
num_test_features = df_test.shape[1]-1

#create temp csv files
df_train.to_csv('train_temp.csv', index=False)
df_test.to_csv('test_temp.csv', index=False)

open('acat_train.csv', 'w').write(str(num_train_entries)+','+str(num_train_features)+','+open('train_temp.csv').read())
open('acat_test.csv', 'w').write(str(num_test_entries)+','+str(num_test_features)+','+open('test_temp.csv').read())
Dataset = collections.namedtuple('Dataset', ['data', 'target'])
Datasets = collections.namedtuple('Datasets', ['train', 'validation', 'test'])

def load_csv(filename, target_dtype, target_column=-1, has_header=True):
    """Load dataset from CSV file."""
    with tf.gfile.Open(filename) as csv_file:
        data_file = csv.reader(csv_file)
        if has_header:
            header = next(data_file)
            n_samples = int(header[0])
            n_features = int(header[1])
            data = np.empty((n_samples, n_features))
            target = np.empty((n_samples,), dtype=np.int)
            for i, ir in enumerate(data_file):
                target[i] = np.asarray(int(eval(ir.pop(target_column))), dtype=target_dtype)
                data[i] = np.asarray(ir, dtype=np.float64)
        else:
            data, target = [], []
            for ir in data_file:
                target.append(ir.pop(target_column))
                data.append(ir)
    return Dataset(data=data, target=target)
#load data into tf
import csv
training_set = load_csv(filename = 'acat_train.csv', target_dtype = np.int, target_column=0)
test_set = load_csv(filename = 'acat_test.csv', target_dtype = np.int, target_column=0)
# import collections
# Dataset = collections.namedtuple('Dataset', ['data', 'target'])
# Datasets = collections.namedtuple('Datasets', ['train', 'validation', 'test'])

# def create_dataset(da, samples, features, target_column = -1):
# #     data = np.empty((samples, features))
# #     target = np.empty((samples,), dtype = np.int)
# #     for i, ir in enumerate(da):
# #         target[i] = np.asarray(ir.pop(target_column), dtype = np.int)
# #         data[i] = np.asarray(ir, dtype = np.int)
#         data, target = [], []
#         for ir in da:
#             target.append(ir.pop(target_column), dtype = np.int)
#             data.append(ir)
#         return Dataset(data=data, target=target)
feature_columns = [tf.contrib.layers.real_valued_column("", dimension=28)]

model_dir = tempfile.mkdtemp() 
print("model directory = %s" % model_dir)

classifier = tf.contrib.learn.DNNClassifier(feature_columns=feature_columns, hidden_units=[10, 20, 10], \
                                            n_classes=5, model_dir=model_dir)
# define tf variables

#training_set = create_dataset(da=df_train, samples=num_train_entries, target_column=0, features=num_train_features)
#test_set = create_dataset(da=df_test, samples=num_test_entries, target_column=0, features=num_test_features)
def get_train_const():
    x = tf.constant(training_set.data)
    y = tf.constant(training_set.target)
    return x, y
def get_test_const():
    x = tf.constant(test_set.data)
    y = tf.constant(test_set.target)
    return x, y
#fit the model
classifier.fit(x = training_set.data, y = training_set.target, steps = 2000)

#evaluate the model
accuracy_score = classifier.evaluate(x = test_set.data, y = test_set.target)["accuracy"]
print("Accuracy : {0:f}".format(accuracy_score))
test = pd.read_csv('topredict.csv', usecols = headers)
for f in headers:
    test[f] = test[f].astype('category')
    test[f].cat.set_categories(categories[f],inplace=True)

new_test = pd.get_dummies(test,columns = headers)
print(new_test)
y = list(classifier.predict(new_test, as_iterable=True))
print('Predictions: {}'.format(str(y)))
print(df_labels[y])