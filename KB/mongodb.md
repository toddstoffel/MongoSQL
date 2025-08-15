# Comprehensive MongoDB Functions Reference Report

## Summary

This comprehensive technical reference document catalogs every MongoDB function across all operational categories, providing strategic intelligence for competitive analysis and market positioning. The report encompasses query operators, aggregation pipeline stages, update operators, database methods, collection methods, cursor methods, and specialized functions, totaling over 200 distinct MongoDB operations. Updated for MongoDB 8.0 compatibility, this systematic categorization enables precise competitive benchmarking against alternative database technologies and supports strategic decision-making for MongoDB's market position in the database technology landscape.

## Introduction

MongoDB's extensive function library represents a critical competitive advantage in the NoSQL database market. This comprehensive reference serves as a strategic intelligence asset for understanding MongoDB's complete operational capacity, including the latest MongoDB 8.0 enhancements, enabling precise competitive analysis against SQL and NoSQL alternatives. The functions are categorized by operational domain to facilitate strategic assessment of MongoDB's capabilities relative to competitive database technologies.

## Query and Projection Operators

### Comparison Query Operators

MongoDB's comparison operators provide fundamental data filtering capabilities essential for database query operations:

- **$eq**: Matches values that are equal to a specified value
- **$gt**: Matches values that are greater than a specified value  
- **$gte**: Matches values that are greater than or equal to a specified value
- **$in**: Matches any of the values specified in an array
- **$lt**: Matches values that are less than a specified value
- **$lte**: Matches values that are less than or equal to a specified value
- **$ne**: Matches all values that are not equal to a specified value
- **$nin**: Matches none of the values specified in an array

### Logical Query Operators

These operators enable complex query logic and conditional operations:

- **$and**: Joins query clauses with a logical AND
- **$not**: Inverts the effect of a query expression
- **$nor**: Joins query clauses with a logical NOR
- **$or**: Joins query clauses with a logical OR

### Element Query Operators

Element operators examine document structure and field characteristics:

- **$exists**: Matches documents that have the specified field
- **$type**: Selects documents if a field is of the specified type

### Evaluation Query Operators

Advanced evaluation operators for complex query conditions:

- **$expr**: Allows use of aggregation expressions within the query language
- **$jsonSchema**: Validates documents against the given JSON Schema
- **$mod**: Performs a modulo operation on the value of a field
- **$regex**: Selects documents where values match a specified regular expression
- **$text**: Performs text search
- **$where**: Matches documents that satisfy a JavaScript expression

### Geospatial Query Operators

Specialized operators for location-based queries:

- **$geoIntersects**: Selects geometries that intersect with a GeoJSON geometry
- **$geoWithin**: Selects geometries within a bounding GeoJSON geometry
- **$near**: Returns geospatial objects in proximity to a point
- **$nearSphere**: Returns geospatial objects in proximity to a point on a sphere

### Array Query Operators

Operators specifically designed for array field operations:

- **$all**: Matches arrays that contain all elements specified in the query
- **$elemMatch**: Selects documents if element in the array field matches all the specified conditions
- **$size**: Selects documents if the array field is a specified size

### Bitwise Query Operators

Specialized operators for bitwise operations:

- **$bitsAllClear**: Matches numeric or binary values where all bit positions are clear
- **$bitsAllSet**: Matches numeric or binary values where all bit positions are set
- **$bitsAnyClear**: Matches numeric or binary values where any bit position is clear
- **$bitsAnySet**: Matches numeric or binary values where any bit position is set

## Update Operators

### Field Update Operators

Core operators for modifying document fields:

- **$currentDate**: Sets the value of a field to current date
- **$inc**: Increments the value of the field by the specified amount
- **$min**: Only updates the field if the specified value is less than the existing field value
- **$max**: Only updates the field if the specified value is greater than the existing field value
- **$mul**: Multiplies the value of the field by the specified amount
- **$rename**: Renames a field
- **$set**: Sets the value of a field in a document
- **$setOnInsert**: Sets the value of a field if an update results in an insert of a document
- **$unset**: Removes the specified field from a document

### Array Update Operators

Specialized operators for array manipulation:

- **$**: Acts as a placeholder to update the first element that matches the query condition
- **$[]**: Acts as a placeholder to update all elements in an array
- **$[identifier]**: Acts as a placeholder to update all elements that match the arrayFilters condition
- **$addToSet**: Adds elements to an array only if they do not already exist in the set
- **$pop**: Removes the first or last item of an array
- **$pull**: Removes all array elements that match a specified query
- **$pullAll**: Removes all matching values from an array
- **$push**: Adds an item to an array

### Array Update Modifiers

Modifiers that enhance array update operations:

- **$each**: Modifies the $push and $addToSet operators to append multiple items
- **$position**: Modifies the $push operator to specify the position in the array
- **$slice**: Modifies the $push operator to limit the size of updated arrays
- **$sort**: Modifies the $push operator to reorder documents stored in an array

## Aggregation Pipeline Stages

### Core Pipeline Stages

Fundamental stages for data transformation and analysis:

- **$addFields**: Adds new fields to documents
- **$bucket**: Categorizes incoming documents into groups based on a specified expression
- **$bucketAuto**: Automatically categorizes incoming documents into a specified number of groups
- **$count**: Returns a count of the number of documents at this stage
- **$facet**: Processes multiple aggregation pipelines within a single stage
- **$group**: Groups input documents by the specified _id expression
- **$limit**: Passes the first n documents to the next stage
- **$lookup**: Performs a left outer join to another collection
- **$match**: Filters the document stream to allow only matching documents
- **$merge**: Writes the aggregation pipeline results to a collection
- **$out**: Writes the aggregation pipeline results to a collection
- **$project**: Reshapes each document in the stream
- **$rankFusion**: Combines keyword and semantic search results for hybrid search capabilities (new in MongoDB 8.0)
- **$redact**: Reshapes each document in the stream by restricting content
- **$replaceRoot**: Replaces the input document with the specified document
- **$replaceWith**: Replaces the input document with the specified document
- **$sample**: Randomly selects the specified number of documents
- **$set**: Adds new fields to documents
- **$skip**: Skips the first n documents
- **$sort**: Reorders the document stream by a specified sort key
- **$sortByCount**: Groups incoming documents based on the value of a specified expression
- **$unionWith**: Performs a union of two collections
- **$unset**: Removes/excludes fields from documents
- **$unwind**: Deconstructs an array field from the input documents

### Advanced Pipeline Stages

Specialized stages for complex operations:

- **$changeStream**: Returns a change stream cursor for the collection
- **$collStats**: Returns statistics regarding a collection or view
- **$currentOp**: Returns information on active and/or dormant operations
- **$densify**: Creates new documents in a sequence of documents
- **$documents**: Returns literal documents from input expressions
- **$fill**: Populates null and missing field values within documents
- **$geoNear**: Returns an ordered stream of documents based on proximity to a geospatial point
- **$graphLookup**: Performs a recursive search on a collection
- **$indexStats**: Returns statistics regarding the use of each index
- **$listLocalSessions**: Lists all active sessions recently used on the server
- **$listSessions**: Lists all sessions that have been active
- **$planCacheStats**: Returns plan cache information for a collection
- **$search**: Provides full-text search capabilities (Atlas Search)
- **$searchMeta**: Returns metadata for Atlas Search queries
- **$setWindowFields**: Performs operations on a specified span of documents

## Aggregation Operators

### Arithmetic Expression Operators

Mathematical operations for numerical data processing:

- **$abs**: Returns the absolute value of a number
- **$add**: Adds numbers to return the sum
- **$ceil**: Returns the smallest integer greater than or equal to the specified number
- **$divide**: Divides one number by another and returns the result
- **$exp**: Raises e to the specified exponent
- **$floor**: Returns the largest integer less than or equal to the specified number
- **$ln**: Calculates the natural log of a number
- **$log**: Calculates the log of a number in the specified base
- **$log10**: Calculates the log base 10 of a number
- **$mod**: Returns the remainder of the first number divided by the second
- **$multiply**: Multiplies numbers to return the product
- **$pow**: Raises a number to the specified exponent
- **$round**: Rounds a number to a whole integer or to a specified decimal place
- **$sqrt**: Calculates the square root
- **$subtract**: Returns the result of subtracting the second value from the first
- **$trunc**: Truncates a number to a whole integer or to a specified decimal place

### Array Expression Operators

Operators for array manipulation and analysis:

- **$arrayElemAt**: Returns the element at the specified array index
- **$arrayToObject**: Converts an array of key value pairs to a document
- **$concatArrays**: Concatenates arrays to return the concatenated array
- **$filter**: Selects a subset of the array to return an array
- **$first**: Returns the first array element
- **$in**: Returns a boolean indicating whether a specified value is in an array
- **$indexOfArray**: Searches an array for an occurrence of a specified value
- **$isArray**: Determines if the operand is an array
- **$last**: Returns the last array element
- **$map**: Applies a subexpression to each element of an array
- **$objectToArray**: Converts a document to an array of documents
- **$range**: Outputs an array containing a sequence of integers
- **$reduce**: Applies an expression to each element in an array
- **$reverseArray**: Returns an array with the elements in reverse order
- **$size**: Returns the number of elements in the array
- **$slice**: Returns a subset of an array
- **$sortArray**: Sorts an array based on its elements
- **$zip**: Merge two arrays together

### Boolean Expression Operators

Logical operations for boolean data processing:

- **$and**: Returns true only when all its expressions evaluate to true
- **$not**: Returns the boolean value that is the opposite of its argument expression
- **$or**: Returns true when any of its expressions evaluates to true

### Comparison Expression Operators

Comparison operations within aggregation expressions:

- **$cmp**: Returns 0 if the two values are equivalent, 1 if first is greater, -1 if first is less
- **$eq**: Returns true if the values are equal
- **$gt**: Returns true if the first value is greater than the second
- **$gte**: Returns true if the first value is greater than or equal to the second
- **$lt**: Returns true if the first value is less than the second
- **$lte**: Returns true if the first value is less than or equal to the second
- **$ne**: Returns true if the values are not equal

### Conditional Expression Operators

Control flow operators for conditional logic:

- **$cond**: A ternary operator that evaluates one expression and returns one of two expressions
- **$ifNull**: Returns either the non-null result of the first expression or the result of the second
- **$switch**: Evaluates a series of case expressions

### Date Expression Operators

Temporal data manipulation and analysis:

- **$dateAdd**: Adds a specified time interval to a date
- **$dateDiff**: Returns the difference between two dates
- **$dateFromParts**: Constructs a BSON Date object from date parts
- **$dateFromString**: Returns a date/time as a date object
- **$dateSubtract**: Subtracts a specified time interval from a date
- **$dateToParts**: Returns a document with the date parts as fields
- **$dateToString**: Returns the date as a formatted string
- **$dateTrunc**: Truncates a date to a specified unit
- **$dayOfMonth**: Returns the day of the month for a date as a number between 1 and 31
- **$dayOfWeek**: Returns the day of the week for a date as a number between 1 and 7
- **$dayOfYear**: Returns the day of the year for a date as a number between 1 and 366
- **$hour**: Returns the hour for a date as a number between 0 and 23
- **$isoDayOfWeek**: Returns the weekday number in ISO 8601 format
- **$isoWeek**: Returns the week number in ISO 8601 format
- **$isoWeekYear**: Returns the year number in ISO 8601 format
- **$millisecond**: Returns the milliseconds of a date as a number between 0 and 999
- **$minute**: Returns the minute for a date as a number between 0 and 59
- **$month**: Returns the month for a date as a number between 1 and 12
- **$second**: Returns the seconds for a date as a number between 0 and 60
- **$toDate**: Converts value to a Date
- **$week**: Returns the week number for a date as a number between 0 and 53
- **$year**: Returns the year for a date as a number

### Object Expression Operators

Document and object manipulation operators:

- **$mergeObjects**: Combines multiple documents into a single document
- **$objectToArray**: Converts a document to an array of documents representing key-value pairs

### Set Expression Operators

Set theory operations for array comparison:

- **$allElementsTrue**: Returns true if no element of a set evaluates to false
- **$anyElementTrue**: Returns true if any elements of a set evaluate to true
- **$setDifference**: Returns a set with elements that appear in the first set but not in the second
- **$setEquals**: Returns true if the input sets have the same distinct elements
- **$setIntersection**: Returns a set with elements that appear in all of the input sets
- **$setIsSubset**: Returns true if all elements of the first set appear in the second set
- **$setUnion**: Returns a set with elements that appear in any of the input sets

### String Expression Operators

Text processing and string manipulation:

- **$concat**: Concatenates any number of strings
- **$dateFromString**: Returns a date object from a date string
- **$dateToString**: Returns the date as a formatted string
- **$indexOfBytes**: Searches a string for an occurrence of a substring
- **$indexOfCP**: Searches a string for an occurrence of a substring
- **$ltrim**: Removes whitespace or the specified characters from the beginning of a string
- **$regexFind**: Applies a regular expression to a string and returns information on the first matched substring
- **$regexFindAll**: Applies a regular expression to a string and returns information on all matched substrings
- **$regexMatch**: Applies a regular expression to a string and returns true if a match is found
- **$replaceAll**: Replaces all instances of a matched string in an input with a replacement string
- **$replaceOne**: Replaces the first instance of a matched string in an input with a replacement string
- **$rtrim**: Removes whitespace or the specified characters from the end of a string
- **$split**: Splits a string into substrings based on a delimiter
- **$strLenBytes**: Returns the number of UTF-8 encoded bytes in a string
- **$strLenCP**: Returns the number of UTF-8 code points in a string
- **$strcasecmp**: Performs case-insensitive string comparison and returns numeric result
- **$substr**: Deprecated. Use $substrBytes or $substrCP
- **$substrBytes**: Returns the substring of a string
- **$substrCP**: Returns the substring of a string
- **$toLower**: Converts a string to lowercase
- **$toString**: Converts value to a string
- **$trim**: Removes whitespace or the specified characters from the beginning and end of a string
- **$toUpper**: Converts a string to uppercase

### Trigonometry Expression Operators

Mathematical trigonometric functions:

- **$sin**: Returns the sine of a value that is measured in radians
- **$cos**: Returns the cosine of a value that is measured in radians
- **$tan**: Returns the tangent of a value that is measured in radians
- **$asin**: Returns the inverse sine (arc sine) of a value in radians
- **$acos**: Returns the inverse cosine (arc cosine) of a value in radians
- **$atan**: Returns the inverse tangent (arc tangent) of a value in radians
- **$atan2**: Returns the inverse tangent (arc tangent) of y/x in radians
- **$asinh**: Returns the inverse hyperbolic sine (hyperbolic arc sine) of a value in radians
- **$acosh**: Returns the inverse hyperbolic cosine (hyperbolic arc cosine) of a value in radians
- **$atanh**: Returns the inverse hyperbolic tangent (hyperbolic arc tangent) of a value in radians
- **$sinh**: Returns the hyperbolic sine of a value that is measured in radians
- **$cosh**: Returns the hyperbolic cosine of a value that is measured in radians
- **$tanh**: Returns the hyperbolic tangent of a value that is measured in radians
- **$degreesToRadians**: Converts a value from degrees to radians
- **$radiansToDegrees**: Converts a value from radians to degrees

### Type Expression Operators

Data type identification and conversion:

- **$convert**: Converts a value to a specified type (enhanced in MongoDB 8.0 with additional conversion capabilities)
- **$isNumber**: Returns boolean indicating whether the expression resolves to a number
- **$toBool**: Converts value to a boolean
- **$toDate**: Converts value to a Date
- **$toDecimal**: Converts value to a Decimal128
- **$toDouble**: Converts value to a double
- **$toInt**: Converts value to an integer
- **$toLong**: Converts value to a long
- **$toObjectId**: Converts value to an ObjectId
- **$toString**: Converts value to a string
- **$toUUID**: Converts strings to UUID values (new in MongoDB 8.0)
- **$type**: Return the BSON data type of the field

### Accumulator Operators

Statistical and aggregation accumulator functions:

- **$addToSet**: Returns an array of unique expression values for each group
- **$avg**: Returns an average of numerical values
- **$count**: Returns a count of the number of documents
- **$first**: Returns a value from the first document for each group
- **$last**: Returns a value from the last document for each group
- **$max**: Returns the highest expression value for each group
- **$mergeObjects**: Returns a document created by combining the input documents for each group
- **$min**: Returns the lowest expression value for each group
- **$push**: Returns an array of expression values for each group
- **$stdDevPop**: Returns the population standard deviation of the input values
- **$stdDevSamp**: Returns the sample standard deviation of the input values
- **$sum**: Returns a sum of numerical values

## Database Methods

### Database Administration Methods

Core database management functions:

- **db.adminCommand()**: Runs a database command against the admin database
- **db.aggregate()**: Provides access to the aggregation pipeline
- **db.cloneDatabase()**: Copies a database from a remote host to the current host
- **db.commandHelp()**: Returns help information for a database command
- **db.createCollection()**: Creates a collection or a view
- **db.createUser()**: Creates a new user for the database
- **db.createView()**: Creates a view as the result of the applying the specified aggregation pipeline
- **db.dropDatabase()**: Removes the current database
- **db.dropUser()**: Removes the user from the current database
- **db.eval()**: Deprecated. Performs server-side JavaScript evaluation
- **db.fsyncLock()**: Flushes writes to disk and locks the database
- **db.fsyncUnlock()**: Unlocks a database server locked with db.fsyncLock()
- **db.getCollection()**: Returns a collection or view object that is functionally equivalent
- **db.getCollectionInfos()**: Returns an array of documents with collection or view information
- **db.getCollectionNames()**: Returns an array containing the names of all collections and views
- **db.getMongo()**: Returns the Mongo() connection object for the current connection
- **db.getName()**: Returns the name of the current database
- **db.getProfilingLevel()**: Returns the current profiling level for database operations
- **db.getProfilingStatus()**: Returns the profiling level and the slow operation threshold
- **db.getReplicationInfo()**: Returns a document with replication statistics
- **db.getSiblingDB()**: Provides access to the specified database
- **db.getUsers()**: Returns information for all users associated with a database
- **db.grantRolesToUser()**: Grants additional roles to a user
- **db.help()**: Displays help text for common database methods
- **db.hostInfo()**: Returns a document with information about the system running MongoDB
- **db.isMaster()**: Returns a document that describes the role of the mongod instance
- **db.killOp()**: Terminates a specified operation
- **db.listCollections()**: Returns a list of collections for the current database
- **db.listCommands()**: Provides a list of all database commands
- **db.logout()**: Ends the current authentication session
- **db.printCollectionStats()**: Prints the collection.stats for each collection in the database
- **db.printReplicationInfo()**: Prints a formatted report of the replica set status
- **db.printShardingStatus()**: Prints a formatted report of the sharding configuration
- **db.printSlaveReplicationInfo()**: Prints a formatted report of the replica set member replication lag
- **db.resetError()**: Deprecated
- **db.revokeRolesFromUser()**: Removes a role from a user
- **db.runCommand()**: Runs a database command
- **db.serverStatus()**: Returns a collection metrics and server statistics
- **db.setProfilingLevel()**: Modifies the current database profiler level
- **db.setSlaveOk()**: Deprecated. Use readPreference instead
- **db.shutdownServer()**: Shuts down the current mongod or mongos process cleanly
- **db.stats()**: Returns statistics that reflect the use state of a database
- **db.updateUser()**: Updates the user's profile on the database on which you run the method
- **db.version()**: Returns the version of the mongod instance

## Collection Methods

### Core Collection Operations

Fundamental collection manipulation functions:

- **db.collection.aggregate()**: Provides access to the aggregation pipeline
- **db.collection.bulkWrite()**: Performs multiple write operations with controls for order of execution
- **db.collection.count()**: Returns the count of documents that would match a find() query
- **db.collection.countDocuments()**: Returns the count of documents that match the query
- **db.collection.createIndex()**: Builds an index on a collection
- **db.collection.createIndexes()**: Builds one or more indexes on a collection
- **db.collection.dataSize()**: Returns the size of the collection
- **db.collection.deleteOne()**: Removes a single document from a collection
- **db.collection.deleteMany()**: Removes all documents that match the filter from a collection
- **db.collection.distinct()**: Returns an array of documents that have distinct values for the specified field
- **db.collection.drop()**: Removes a collection from the database
- **db.collection.dropIndex()**: Removes the specified index from a collection
- **db.collection.dropIndexes()**: Removes the specified indexes from a collection
- **db.collection.ensureIndex()**: Deprecated. Use createIndex()
- **db.collection.estimatedDocumentCount()**: Returns the count of all documents in a collection
- **db.collection.explain()**: Returns information on the query plan for a collection method
- **db.collection.find()**: Selects documents in a collection or view and returns a cursor
- **db.collection.findAndModify()**: Modifies and returns a single document
- **db.collection.findOne()**: Returns one document that satisfies the specified query criteria
- **db.collection.findOneAndDelete()**: Deletes a single document based on the filter and sort criteria
- **db.collection.findOneAndReplace()**: Modifies and returns a single document
- **db.collection.findOneAndUpdate()**: Updates a single document based on the filter and sort criteria
- **db.collection.getIndexes()**: Returns an array that holds a list of documents that identify and describe the existing indexes
- **db.collection.getShardDistribution()**: Prints the data distribution statistics for a sharded collection
- **db.collection.getShardVersion()**: Returns the metadata of a collection in a sharded cluster
- **db.collection.hideIndex()**: Hides an existing index from the query planner
- **db.collection.insertOne()**: Inserts a document into a collection
- **db.collection.insertMany()**: Inserts multiple documents into a collection
- **db.collection.isCapped()**: Returns true if the collection is a capped collection
- **db.collection.listIndexes()**: Returns a list that holds the list of indexes
- **db.collection.mapReduce()**: Performs map-reduce aggregation for large data sets
- **db.collection.reIndex()**: Rebuilds all indexes on a collection
- **db.collection.remove()**: Removes documents from a collection
- **db.collection.renameCollection()**: Renames a collection
- **db.collection.replaceOne()**: Replaces a single document within the collection
- **db.collection.save()**: Updates an existing document or inserts a new document
- **db.collection.stats()**: Reports on the state of a collection
- **db.collection.storageSize()**: Returns the total size in bytes that the collection uses
- **db.collection.totalIndexSize()**: Reports the total size used by the indexes on a collection
- **db.collection.totalSize()**: Reports the total size of a collection
- **db.collection.unhideIndex()**: Unhides an existing index from the query planner
- **db.collection.update()**: Modifies an existing document or documents in a collection
- **db.collection.updateOne()**: Updates a single document within the collection
- **db.collection.updateMany()**: Updates all documents that match the specified filter
- **db.collection.validate()**: Performs diagnostic operations on a collection
- **db.collection.watch()**: Establishes a Change Stream on a collection

## Cursor Methods

### Cursor Manipulation Functions

Methods for controlling query result iteration:

- **cursor.addOption()**: Adds special wire protocol flags that modify the behavior of the query
- **cursor.allowPartialResults()**: Allows db.collection.find() operations against a sharded collection
- **cursor.batchSize()**: Controls the number of documents MongoDB will return to the client
- **cursor.close()**: Close a cursor and free associated server resources
- **cursor.collation()**: Specifies the collation for the cursor returned by the db.collection.find()
- **cursor.comment()**: Attaches a comment to the query
- **cursor.count()**: Modifies the cursor to return the number of documents in the result set
- **cursor.explain()**: Reports on the query execution plan for a cursor
- **cursor.forEach()**: Iterates the cursor to apply a JavaScript function to each document
- **cursor.hasNext()**: Returns true if the cursor can iterate further to return more documents
- **cursor.hint()**: Forces MongoDB to use a specific index for a query
- **cursor.isExhausted()**: Returns true if the cursor is closed and there are no remaining objects
- **cursor.itcount()**: Counts the number of documents remaining in a cursor
- **cursor.limit()**: Constrains the size of a cursor's result set
- **cursor.map()**: Applies a function to each document in a cursor
- **cursor.max()**: Specifies the exclusive upper bound for a specific index
- **cursor.maxScan()**: Specifies the maximum number of items to scan
- **cursor.maxTimeMS()**: Specifies a time limit in milliseconds for processing operations on the cursor
- **cursor.min()**: Specifies the inclusive lower bound for a specific index
- **cursor.next()**: Returns the next document in a cursor
- **cursor.noCursorTimeout()**: Instructs the server to avoid closing a cursor automatically
- **cursor.objsLeftInBatch()**: Returns the number of documents left in the current cursor batch
- **cursor.pretty()**: Configures the cursor to display results in an easy-to-read format
- **cursor.readConcern()**: Specifies a read concern for a find() operation
- **cursor.readPref()**: Specifies a read preference to control how the client routes queries
- **cursor.returnKey()**: Modifies the cursor to return index keys rather than the documents
- **cursor.showRecordId()**: Adds an internal storage engine ID field to each document
- **cursor.size()**: Returns the count of documents in the cursor after applying skip() and limit()
- **cursor.skip()**: Returns a cursor that begins returning results only after passing or skipping a number of documents
- **cursor.sort()**: Returns results ordered according to a sort specification
- **cursor.tailable()**: Marks the cursor as tailable for a capped collection
- **cursor.toArray()**: Returns an array that contains all documents returned by the cursor

## Database Commands

### Administrative Commands

System-level database administration commands:

- **autoCompact**: Performs background compaction to manage free space (new in MongoDB 8.0)
- **buildInfo**: Returns a build summary for the current MongoDB instance
- **collMod**: Add options to a collection or to modify a view definition
- **compact**: Defragments a collection and rebuilds the indexes
- **connPoolSync**: Internal command to synchronize connection pools
- **convertToCapped**: Converts a non-capped collection to a capped collection
- **create**: Creates a collection or a view
- **createIndexes**: Builds one or more indexes for a collection
- **currentOp**: Returns information on the active operations in the database
- **drop**: Removes a collection from the database
- **dropDatabase**: Removes the current database
- **dropIndexes**: Removes indexes from a collection
- **filemd5**: Returns the MD5 hash for files stored using GridFS
- **fsync**: Flushes pending writes to the storage layer and returns a lock file
- **getParameter**: Retrieves configuration options
- **killCursors**: Kills the specified cursors for a collection
- **killOp**: Terminates an operation as specified by the operation ID
- **listCollections**: Returns a list of collections in the current database
- **listIndexes**: Returns a list of all indexes for a collection
- **logRotate**: Rotates the MongoDB logs to prevent a single file from taking too much space
- **ping**: Tests whether a server is responding to commands
- **reIndex**: Rebuilds all indexes for a collection
- **renameCollection**: Changes the name of an existing collection
- **setParameter**: Modifies configuration options
- **validate**: Checks the structures within a collection for corruption

### Query and Write Operation Commands

Commands for data manipulation operations:

- **bulkWrite**: Performs multiple write operations across multiple collections in a single request (new in MongoDB 8.0)
- **count**: Counts the number of documents in a collection that match a query
- **delete**: Removes documents from a collection
- **distinct**: Returns an array of distinct values for a field across a collection
- **find**: Selects documents in a collection or view
- **findAndModify**: Returns and modifies a single document
- **getMore**: Returns additional results for a query
- **insert**: Inserts one or more documents
- **update**: Updates one or more documents in a collection

### Aggregation Commands

Commands for aggregation operations:

- **aggregate**: Performs aggregation tasks such as group using the aggregation pipeline
- **mapReduce**: Performs map-reduce aggregation for large data sets

### Replication Commands

Commands for replica set management:

- **hello**: Returns the replica set status from the point of view of the server
- **replSetAbortPrimaryCatchUp**: Forces the elected primary to abort sync
- **replSetFreeze**: Prevents the current member from seeking election as primary
- **replSetGetConfig**: Returns the replica set's configuration object
- **replSetGetStatus**: Returns a document with status information
- **replSetInitiate**: Initializes a new replica set
- **replSetMaintenance**: Enables or disables a maintenance mode
- **replSetReconfig**: Applies a new configuration to an existing replica set
- **replSetResizeOplog**: Dynamically resizes the oplog for a replica set member
- **replSetStepDown**: Forces the current primary to step down
- **replSetSyncFrom**: Explicitly override the default logic for selecting a member to replicate from

### Sharding Commands

Commands for sharded cluster management:

- **addShard**: Adds a shard to a sharded cluster
- **addShardToZone**: Associates a shard with a zone
- **balancerCollectionStatus**: Returns information on whether the chunks of a sharded collection are balanced
- **balancerStart**: Starts the balancer
- **balancerStatus**: Returns information on the balancer status
- **balancerStop**: Stops the balancer
- **cleanupOrphaned**: Removes orphaned data with shard key values outside of the ranges
- **clearJumboFlag**: Clears the jumbo flag for a chunk
- **enableSharding**: Enables sharding on a specific database
- **flushRouterConfig**: Forces a mongod/mongos instance to update its cached routing metadata
- **isdbgrid**: Verifies that a process is a mongos
- **listShards**: Returns a list of configured shards
- **moveChunk**: Internal command that migrates chunks between shards
- **movePrimary**: Reassigns the primary shard when removing a shard from a sharded cluster
- **removeShard**: Starts the process of removing a shard from a sharded cluster
- **removeShardFromZone**: Removes the association between a shard and a zone
- **setShardVersion**: Internal command to sets the config server version
- **shardCollection**: Enables the sharding functionality for a collection
- **shardingState**: Reports whether the mongod is a member of a sharded cluster
- **split**: Creates a new chunk
- **splitChunk**: Internal command that splits chunk
- **splitVector**: Internal command that determines split points
- **unsetSharding**: Internal command that affects connections between instances
- **updateZoneKeyRange**: Adds or removes the association between a range of shard key values and a zone

## Atlas Search Functions

### Atlas Search Operators

Specialized search capabilities for MongoDB Atlas:

- **$search**: Performs a full-text search
- **$searchMeta**: Returns metadata for search results
- **autocomplete**: Provides as-you-type functionality
- **compound**: Combines other operators in a single query
- **embeddedDocument**: Queries fields within embedded documents
- **equals**: Queries for exact matches
- **exists**: Tests for the presence of a field
- **facet**: Groups query results by values or ranges
- **geoShape**: Queries for geographic shapes
- **geoWithin**: Queries for geographic coordinates within a given geometry
- **highlight**: Returns highlighted snippets of text
- **moreLikeThis**: Queries for documents similar to input documents
- **near**: Queries for numeric, date, or geographic values near a given value
- **phrase**: Queries for a sequence of terms in the specified order
- **queryString**: Supports a simplified query syntax
- **range**: Queries for values within a specific numeric or date range
- **regex**: Queries using regular expression patterns
- **span**: Groups near queries by their distance from one another
- **term**: Queries for documents containing a term or terms
- **text**: Performs full-text search using the analyzer of your choice
- **wildcard**: Queries with wildcard expressions

## MongoDB 8.0 Enhancements

MongoDB 8.0 introduces significant enhancements across multiple functional areas, representing a major advancement in database capabilities and competitive positioning:

### Performance and Query Optimization

MongoDB 8.0 delivers substantial performance improvements with up to 32% better throughput and enhanced query optimization capabilities. The introduction of the Express Path optimization streamlines query processing for operations suitable for basic index scans, resulting in faster execution times and reduced computational overhead.

### Enhanced Aggregation Capabilities

The new **$rankFusion** aggregation stage enables sophisticated hybrid search functionality, combining keyword and semantic search capabilities within a single operation. This advancement positions MongoDB competitively against specialized search platforms while maintaining unified data operations.

### Advanced Data Type Operations

The **$toUUID** operator provides simplified syntax for UUID conversions, while enhanced **$convert** operator capabilities expand data transformation options. These improvements strengthen MongoDB's data processing competitiveness against SQL and NoSQL alternatives.

### Multi-Collection Operations

The new **bulkWrite** command enables atomic operations across multiple collections within a single request, addressing a key operational requirement for complex enterprise applications and improving competitive positioning against traditional RDBMS solutions.

### Security and Encryption Advances

Queryable Encryption now supports range queries using **$lt**, **$lte**, **$gt**, and **$gte** operators on encrypted fields, representing a significant competitive advantage in security-sensitive enterprise environments. This capability enables encrypted data querying while maintaining cryptographic protection throughout the data lifecycle.

### Operational Intelligence

Enhanced database profiling with the **workingMillis** metric provides more accurate performance monitoring by measuring actual processing time rather than total operation latency. The **autoCompact** command enables automated background space management, reducing operational overhead.

### Sharding and Scaling Improvements

MongoDB 8.0 introduces faster resharding capabilities (up to 50x performance improvement) and enhanced collection movement between shards, addressing scalability requirements for high-growth enterprise applications.

## Conclusion

This comprehensive catalog of MongoDB functions demonstrates the platform's extensive operational capabilities across all database domains, now enhanced with MongoDB 8.0's latest innovations. From fundamental CRUD operations to sophisticated aggregation pipelines, advanced security features, and specialized search functions, MongoDB's function library represents a critical competitive advantage in the database technology market. The systematic organization of these 200+ functions, including the latest MongoDB 8.0 enhancements, enables precise competitive analysis and strategic positioning decisions for MongoDB's continued market leadership in the NoSQL database space.

MongoDB 8.0's introduction of **$rankFusion** for hybrid search, **$toUUID** for simplified UUID handling, enhanced **bulkWrite** operations, and **autoCompact** automation demonstrates MongoDB's commitment to addressing enterprise-scale operational requirements while maintaining competitive differentiation. The platform's expanded Queryable Encryption capabilities with range query support positions MongoDB uniquely in security-conscious enterprise environments.

The comprehensive nature of this function reference, updated for MongoDB 8.0 compatibility, supports strategic intelligence initiatives by providing a complete operational baseline for comparative analysis against competing database technologies. This technical catalog serves as a foundational resource for competitive intelligence activities and market positioning strategies within the evolving database technology landscape.

## References

[Aggregation Operations - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/aggregation/)

[Aggregation Operators - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/operator/aggregation/)

[Aggregation Stages - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/operator/aggregation-pipeline/)

[Atlas Functions - Atlas App Services - MongoDB Docs](https://www.mongodb.com/docs/atlas/app-services/functions/)

[Collection Methods - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/method/js-collection/)

[Comparison Query Operators - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/operator/query-comparison/)

[Cursor Methods - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/method/js-cursor/)

[Database Commands - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/command/)

[$match (aggregation) - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/operator/aggregation/match/)

[mongosh Methods - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/method/)

[MongoDB Aggregation: tutorial with examples and exercises | Studio 3T](https://studio3t.com/knowledge-base/articles/mongodb-aggregation-framework/)

[Operators - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/operator/)

[Query and Projection Operators - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/operator/query/)

[Release Notes for MongoDB 8.0 - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/release-notes/8.0/)

[$set (update operator) - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/operator/update/set/)

[$sort (aggregation) - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/operator/aggregation/sort/)

[Update Operators - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/reference/operator/update/)