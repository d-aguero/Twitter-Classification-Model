
install.packages("tm")
library(tm)
install.packages("e1071")
library(e1071)


############################
# Part 1
# Preparing the data


setwd("C:/Users/Alex/Desktop/school/LING460/Proj3")
users = read.csv("bbcdoctorwho_tweets.csv", encoding = "UTF-8")


# "users" has two fields: "age" and "tweets"
# "age" is the age of the user who authored the tweets.
# "tweets" is one large string of up to 800 recent tweets by the user.

# First, the tweets need to be split up into words:
users$tweets = as.character(users$tweets)
users$words = strsplit(users$tweets, " ")

# Next, clean data to remove non-words, and rebuild text to be corpus-friendly:
for (i in 1:length(users$words)){
  users$words[[i]] = gsub(pattern="^@.*", "", users$words[[i]], ignore.case=TRUE)
  users$words[[i]] = gsub(pattern="^https.*", "", users$words[[i]], ignore.case=TRUE)
  users$words[[i]] = gsub(pattern=".*…$", "", users$words[[i]], ignore.case=TRUE)
  users$words[[i]] = gsub(pattern="[[:punct:]]", "", users$words[[i]], ignore.case=TRUE)
  users$words[[i]] = gsub(pattern="’", "", users$words[[i]], ignore.case=TRUE)
  users$words[[i]] = gsub(pattern=".*\\W.*", "", users$words[[i]], ignore.case=TRUE)
  
  users$words[[i]] = users$words[[i]][users$words[[i]] != ""] # Erase empty strings that resulted from the above
  users$words[[i]] = tolower(users$words[[i]])
  
  users$tweets[[i]] = paste(users$words[[i]], collapse=" ") # Rebuild tweets to be corpus-friendly!
}

good_users = subset(users, age == 22)
curr_row = 1

for (i in 1:length(users$age)){
  if (length(users[i,]$words[[1]]) > 100){
    good_users[curr_row,] = users[i,]
    curr_row = curr_row + 1
  }
}

users = good_users

# I'm dividing into 2 groups based on age.
# Group 1 = 22 or younger
# Group 0 = Older than 22
users$numeric_sentiment = factor(ifelse(users$age > 22, 0, 1))
users$sentiment = factor(ifelse(users$age>22, "Old", "Young"))


#create a corpus object using the function "Corpus" from the tm package. 
tweet.corpus <- Corpus(VectorSource(users$tweets))

cleaning.profile.bin <- list(removePunctuation=T,
                             stripWhitespace=T,
                             removeNumbers=T,
                             tolower=T, 
                             stopwords=T,
                             stemDocument=T,
                             weighting=weightBin) #this does not seem to work

#Create a document-Term Matrix using the cleaning profile above
DTM <-DocumentTermMatrix(tweet.corpus,control=cleaning.profile.bin)

#remove sparse terms.
DTM2 <- removeSparseTerms(DTM, 0.8)

#Save the DTM object as a matrix
DTM.matrix <- as.matrix(DTM2)

############################
# Part 2 
# Dividing the data into training and testing

#We can do that by randomly selecting 80% of numbers between 0 and the length of the corpus (2000),
#and then using those numbers as indicies for selecting the training data
n <- length(tweet.corpus)
#select 80% of numbers from 1 to n
training <- sample(1:n, 0.8*n)
#use the remainder for testing 
testing <- c(1:n)[-training]

#training set = the rows of the DTM matrix at the indicies that were selected for training:
training.set <- DTM.matrix[training, ]

#select the labels of the training examples
training.labels <- users[training, ]$numeric_sentiment

#create a testing set and testing labels:
testing.set <- DTM.matrix[testing, ]
testing.labels <- users[testing, ]$numeric_sentiment

###########################################
# Part 3  
# Applying the Naive Bayes Learner


# run the function "naiveBayes" on the training set paired with training labels:
naive.bayes <- naiveBayes(training.set, training.labels)

#Step 3:  Testing the model: getting predicted labels
bayes.predictions <- predict(naive.bayes,
                             testing.set, type="class")

########################
# Part 4 
# Evaluating performance


#Recall our evaluation function. Let's introduce a few changes:
evaluate <- function(true, predicted){
  
  error <- table(true,predicted)
  
  tp <- error[2,2]  #true positives
  fp <- error[1,2]  #false positives
  tn <- error[1,1]  #true negatives
  fn <- error[2,1]  #false negatives
  
  accuracy <- (tp + tn)/(tp + fp + tn + fn)
  p <- tp/(tp + fp)
  r <- tp/(tp + fn)
  pn <- tn/(tn+fn)
  rn <- tn/(tn+fp)
  fp <- (2*p*r) / (p+r)  #harmonic mean of precision and recall for positive examples
  fn <- (2*pn*rn) /(pn+rn) #haromonic mean of precision and recall for negative examples
  measures <- c("Accuracy" = accuracy, "Fpos" = fp, "Fneg" = fn, "Precision" = p, "Recall" = r)
  
  return(measures)
  
}

#look at the contingency table for the performance 
table(users$numeric_sentiment[testing],bayes.predictions)

#run the evaluate funcion 
evaluate(users$numeric_sentiment[testing],bayes.predictions)
