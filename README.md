
# What is it?

Component of a papers recommender system in a multilingual and multidisciplinary scope.


Designed to be customizable in many ways:

- sentence-transformer model
- the maximum number of candidate articles for the evaluation of semantic similarity
- accepts any type of document that has bibliographic references


# Dependencies

- sentence-transformer
- celery
- mongoengine


# Model

The algorithm adopted is a combination of recommender systems graph based and content based filtering with semantic similarity

The identification of the relationship between scientific articles is made during the document's entry into the system through the common bibliographic references. Subsequently, the documents are ranked by semantic similarity and recorded in a database.

The recommendation system works in two steps: creating links between articles via common citations and assigning a similarity coefficient for a selection of these linked articles. 

The system itself does not establish which articles should be recommended. 

The recommendation system client defines which articles to present as a recommendation depending on the criticality of the use case.


# Note

Result of the Coursework of MBA in Data Science and Analytics - USP / ESALQ - 2020-2022.