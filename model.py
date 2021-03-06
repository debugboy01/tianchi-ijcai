# model for the train file
import pickle
import numpy as np
from sklearn import preprocessing
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

trainsetfile = '/home/wanghao/Document/tianchi/trainset/samplefrom7to10.pkl'
X = []
label = []

rfile = open(trainsetfile, 'rb')
matrix = pickle.load(rfile)

for sample in matrix :
    X.append(sample[0:-1])
    label.append(sample[-1])


scalaX = preprocessing.scale(X)

# model
print "train by RF  model"
#LRmodel = LogisticRegression(C=1, penalty='l1', tol=0.001, max_iter=20000)
RFmodel = RandomForestClassifier(n_estimators=100)
#LRmodel.fit(scalaX, label)
RFmodel.fit(scalaX, label)
print 'RF model finsh '
y_predict = RFmodel.predict(scalaX)
accy =  accuracy_score(label, y_predict )
print "Train set Accuracy " , accy


# predict
print "predict by LR model"


rfile = open('/home/wanghao/Document/tianchi/testset/featureall.pkl', 'rb')
UML_feature = pickle.load(rfile)
UML_predictlabel = {}
UML_pair = []
testX = []
for key in UML_feature.keys():
    testX.append(UML_feature[key])
    UML_pair.append(key)
rfile.close()
UML_pairset = set(UML_pair)
testscaleX = preprocessing.scale(testX)
testpredictY = RFmodel.predict(testscaleX)

for i in range(0,len(UML_pair)):
    UML_predictlabel[UML_pair[i]] = testpredictY[i]

location_merchants = {}
merchantinfo_file = '/home/wanghao/Document/tianchi/tianchi_dataset/ijcai2016_merchant_info'

## predict over

# get the location : merchant
with open(merchantinfo_file, 'rb') as f:

    for line in f :
        line = line.strip('\r\n')
        merchant, budget, locations = line.split(',')
        location = locations.split(':')
        for loc in location :
            if not location_merchants.has_key(loc):
                location_merchants[loc] = []
            location_merchants[loc].append(merchant)

# train : get the user : merchant
UserMerchantRateMatrix = {}
file = '/home/wanghao/Document/tianchi/tianchi_dataset/ijcai2016_koubei_train'
with open(file, 'rb') as f:
    for line in f:
        user, merchant, location, time = line.split(',')
        if not UserMerchantRateMatrix.has_key(user):
            UserMerchantRateMatrix[user] = {}
        if not UserMerchantRateMatrix[user].has_key(merchant):
            UserMerchantRateMatrix[user][merchant] = 0
        UserMerchantRateMatrix[user][merchant] = UserMerchantRateMatrix[user][merchant] + 1

######
Location_merchant_users =  {}
Location_merchant_nums = {}

with open(file, 'rb') as f:

    # get the {  location: {merchant ; [user1, user2,...userN]} }
    for line in f:
        user, merchant, location, time = line.split(',')
        if not Location_merchant_users.has_key(location):
            Location_merchant_users[location] = {}
        if not Location_merchant_users[location].has_key(merchant):
            Location_merchant_users[location][merchant] = []
        if user not in Location_merchant_users[location][merchant]:
            Location_merchant_users[location][merchant].append(user)

     # get the location { merchant : nums }
    for location, merchant_users in Location_merchant_users.items():

        if not Location_merchant_nums.has_key(location):
            Location_merchant_nums[location] = {}

        for merchant, users in merchant_users.items():
            nums = len(users)
            Location_merchant_nums[location][merchant] = nums

    # involve the merchant info
    with open(merchantinfo_file, 'rb') as f :
        for line in f :
            line = line.strip('\r\n')
            merchant, budget, locationlists = line.split(',')
            for location in locationlists.split(':'):
                if not Location_merchant_nums.has_key(location):
                    Location_merchant_nums[location] = {}
                if not Location_merchant_nums[location].has_key(merchant):
                    Location_merchant_nums[location][merchant] = 0

# test
with open('/home/wanghao/Document/tianchi/tianchi_dataset/ijcai2016_koubei_test','rb') as f:
    Allresult = []
    count = 0
    recommendcount = 0
    allrecommendcount = 0
    usercommendcount = 0
    for line in f :
        line = line.strip('\r\n')
        user, location = line.split(',')
        resultMerchant = []


        ###########################################################
        if not UserMerchantRateMatrix.has_key(user):
            # the train file does not include the user
            if len(Location_merchant_nums[location]) < 3:
                for m in Location_merchant_nums[location]:
                    # if self.Location_merchant_nums[location][m] > 0:
                    resultMerchant.append(m)
            else:
                sortedMerchant = sorted(Location_merchant_nums[location].iteritems(), key=lambda d: d[1],reverse=True)[0:3]
                for m in sortedMerchant:
                    resultMerchant.append(m[0])
        else:

            candidateMerchants = location_merchants[location]

            candidateUMLpair = []
            for merchant in candidateMerchants:
                candidateUMLpair.append((user, merchant, location))

            paircount = 0
            for pair in candidateUMLpair:
                if pair in UML_pairset:
                    paircount += 1

            usercommendcount += 1

            if paircount > 0:
                currentUML = []
                for candidateM in candidateUMLpair:
                    if candidateM in UML_pairset:
                        currentUML.append(candidateM)
                        if UML_predictlabel[candidateM] == 1:
                            resultMerchant.append(candidateM[1])

                vistedmerchant = set()
                for t in currentUML:
                    vistedmerchant.add(t[1])

                allrecommendcount += 1

                if len(resultMerchant) == 0 :
                    if len(Location_merchant_nums[location]) < 3:
                        for m in Location_merchant_nums[location]:
                            if  m not in vistedmerchant:
                                resultMerchant.append(m)
                    else:
                        sortedMerchant = sorted(Location_merchant_nums[location].iteritems(), key=lambda d: d[1],reverse=True)
                        merchantcount = 0
                        for m in sortedMerchant:
                            if m[0] not in vistedmerchant:
                                resultMerchant.append(m[0])
                                merchantcount += 1
                                if merchantcount > 2:
                                    break
                else:
                    recommendcount += 1

            else:
                userVisitedMerchants = UserMerchantRateMatrix[user].keys()
                for m in userVisitedMerchants:
                    if Location_merchant_nums[location].has_key(m):
                        resultMerchant.append(m)

                if len(resultMerchant) == 0:
                    if len(Location_merchant_nums[location]) < 3:
                        for m in Location_merchant_nums[location]:
                            if Location_merchant_nums[location][m] > 0:
                                resultMerchant.append(m)
                    else:
                        sortedMerchant = sorted(Location_merchant_nums[location].iteritems(), key=lambda d: d[1],reverse=True)[0:3]
                        for m in sortedMerchant:
                            resultMerchant.append(m[0])

        # add the result to allresult
        result = []
        result.append(user)
        result.append(location)
        string = ''
        for m in resultMerchant:
            string = string + m + ":"
        string = string[0:len(string) - 1]
        result.append(string)

        Allresult.append(result)

        print count
        count += 1

resultfile = '/home/wanghao/Document/tianchi/result/newresult.csv'
import csv
with open(resultfile, 'wb') as f:
    writer = csv.writer(f)
    writer.writerows(Allresult)

print "the recommend num",recommendcount
print "the all recommend num ", allrecommendcount
print "user recommend num " , usercommendcount









