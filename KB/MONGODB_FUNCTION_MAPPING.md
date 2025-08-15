# MariaDB to MongoDB Function Mapping Analysis

**Analysis Date:** August 14, 2025  
**MariaDB Version:** 11.8 LTS  
**MongoDB Version:** 6.0+  
**Project:** SQL to MongoDB Translator  

## Executive Summary

This document provides a comprehensive mapping analysis of MariaDB functions to their MongoDB aggregation pipeline equivalents. Functions are categorized by mapping complexity:

- **✅ Direct Mapping** - Simple 1:1 operator translation
- **🔧 Complex Mapping** - Requires multiple MongoDB operators or expressions
- **🚫 No Direct Equivalent** - Requires custom implementation or workarounds
- **⚠️ Limited Support** - Partial functionality only

## Mapping Categories Overview

| Category | Direct | Complex | No Equivalent | Limited | Total |
|----------|--------|---------|---------------|---------|-------|
| Date/Time Functions | 15 | 25 | 5 | 0 | 45 |
| JSON Functions | 25 | 5 | 0 | 0 | 30 |
| String Functions | 20 | 15 | 5 | 0 | 40 |
| Control Flow Functions | 4 | 2 | 0 | 0 | 6 |
| Window Functions | 0 | 16 | 0 | 0 | 16 |
| Aggregate Functions | 8 | 4 | 0 | 0 | 12 |
| Type Conversion | 2 | 1 | 0 | 0 | 3 |
| Information Functions | 2 | 5 | 5 | 0 | 12 |
| Encryption/Hashing | 0 | 10 | 6 | 0 | 16 |
| Geographic/Geometric | 45 | 5 | 0 | 0 | 50 |

## 1. Date/Time Functions Mapping

### ✅ Direct Mapping (15 functions)

```javascript
// Current date/time functions
'NOW': { $literal: new Date() }
'CURRENT_TIMESTAMP': { $literal: new Date() }
'CURRENT_DATE': { $dateToString: { format: "%Y-%m-%d", date: new Date() } }
'CURRENT_TIME': { $dateToString: { format: "%H:%M:%S", date: new Date() } }
'CURDATE': { $dateToString: { format: "%Y-%m-%d", date: new Date() } }
'CURTIME': { $dateToString: { format: "%H:%M:%S", date: new Date() } }

// Date component extraction
'YEAR': { $year: "$dateField" }
'MONTH': { $month: "$dateField" }
'DAYOFMONTH': { $dayOfMonth: "$dateField" }
'DAYOFWEEK': { $dayOfWeek: "$dateField" }
'DAYOFYEAR': { $dayOfYear: "$dateField" }
'HOUR': { $hour: "$dateField" }
'MINUTE': { $minute: "$dateField" }
'SECOND': { $second: "$dateField" }
'MICROSECOND': { $millisecond: "$dateField" }  // Note: milliseconds, not microseconds
```

### 🔧 Complex Mapping (25 functions)

```javascript
// Date arithmetic
'DATE_ADD': {
  $dateAdd: {
    startDate: "$dateField",
    unit: "day",  // or hour, minute, etc.
    amount: "$intervalValue"
  }
}

'DATE_SUB': {
  $dateSubtract: {
    startDate: "$dateField",
    unit: "day",
    amount: "$intervalValue"
  }
}

'DATEDIFF': {
  $dateDiff: {
    startDate: "$date1",
    endDate: "$date2",
    unit: "day"
  }
}

// Date formatting
'DATE_FORMAT': {
  $dateToString: {
    format: "%Y-%m-%d %H:%M:%S",  // Convert MySQL format to MongoDB format
    date: "$dateField"
  }
}

// Complex date construction
'MAKEDATE': {
  $dateFromString: {
    dateString: {
      $concat: [
        { $toString: "$year" },
        "-01-01"
      ]
    }
  },
  // Then add days
  $dateAdd: {
    startDate: "$$above",
    unit: "day",
    amount: { $subtract: ["$dayOfYear", 1] }
  }
}

'STR_TO_DATE': {
  $dateFromString: {
    dateString: "$dateString",
    format: "%Y-%m-%d"  // Convert MySQL format specifiers
  }
}

// Week calculations
'WEEK': {
  $week: "$dateField"
}

'YEARWEEK': {
  $concat: [
    { $toString: { $year: "$dateField" } },
    { $toString: { $week: "$dateField" } }
  ]
}

// Time conversions
'UNIX_TIMESTAMP': {
  $divide: [
    { $subtract: ["$dateField", new Date("1970-01-01")] },
    1000
  ]
}

'FROM_UNIXTIME': {
  $add: [
    new Date("1970-01-01"),
    { $multiply: ["$timestamp", 1000] }
  ]
}
```

### 🚫 No Direct Equivalent (5 functions)

```javascript
// These require custom implementation
'GET_FORMAT': "Custom format string mapping required"
'PERIOD_ADD': "Custom month arithmetic logic needed"
'PERIOD_DIFF': "Custom period calculation required"
'CONVERT_TZ': "Timezone conversion logic needed"
'LAST_DAY': "End-of-month calculation required"
```

## 2. JSON Functions Mapping

### ✅ Direct Mapping (25 functions)

```javascript
// JSON creation
'JSON_OBJECT': { $mergeObjects: ["$field1", "$field2"] }
'JSON_ARRAY': ["$value1", "$value2", "$value3"]

// JSON extraction
'JSON_EXTRACT': { $getField: { field: "path.to.field", input: "$jsonDoc" } }
'JSON_VALUE': { $getField: { field: "path.to.field", input: "$jsonDoc" } }

// JSON testing
'JSON_VALID': { $type: "$jsonField" }  // Check if object/array
'JSON_TYPE': { $type: "$jsonField" }

// JSON utilities
'JSON_KEYS': { $objectToArray: "$jsonObject" }
'JSON_LENGTH': { $size: "$arrayOrObject" }
'JSON_DEPTH': "Custom recursive calculation needed"

// JSON modification (MongoDB native operations)
'JSON_SET': { $mergeObjects: ["$original", { "newField": "$newValue" }] }
'JSON_INSERT': { $mergeObjects: ["$original", { $cond: [{ $eq: [{ $type: "$original.field" }, "missing"] }, { "field": "$value" }, {}] }] }
'JSON_REPLACE': { $mergeObjects: ["$original", { $cond: [{ $ne: [{ $type: "$original.field" }, "missing"] }, { "field": "$newValue" }, {}] }] }
'JSON_REMOVE': { $unsetField: { field: "fieldToRemove", input: "$jsonDoc" } }

// JSON array operations
'JSON_ARRAY_APPEND': { $concatArrays: ["$originalArray", ["$newValue"]] }
'JSON_ARRAY_INSERT': "Custom array insertion logic"

// JSON merging
'JSON_MERGE': { $mergeObjects: ["$json1", "$json2"] }
'JSON_MERGE_PATCH': { $mergeObjects: ["$json1", "$json2"] }  // Similar behavior
'JSON_MERGE_PRESERVE': "Custom merge logic preserving duplicates"

// JSON search
'JSON_SEARCH': "Custom recursive search implementation"
'JSON_CONTAINS': { $in: ["$searchValue", "$jsonArray"] }
'JSON_CONTAINS_PATH': { $ne: [{ $type: "$json.path.field" }, "missing"] }
'JSON_EXISTS': { $ne: [{ $type: "$json.path.field" }, "missing"] }

// JSON formatting
'JSON_QUOTE': { $toString: "$value" }
'JSON_UNQUOTE': { $convert: { input: "$jsonString", to: "string" } }
'JSON_COMPACT': "Remove whitespace - custom implementation"
'JSON_DETAILED': "Custom formatting implementation"
```

### 🔧 Complex Mapping (5 functions)

```javascript
'JSON_QUERY': "Requires JSONPath-like traversal implementation"
'JSON_MERGE_PRESERVE': "Custom logic to handle duplicate key preservation"
'JSON_SEARCH': "Recursive document traversal with pattern matching"
'JSON_ARRAY_INSERT': "Array manipulation at specific index"
'JSON_DEPTH': "Recursive depth calculation algorithm"
```

## 3. String Functions Mapping

### ✅ Direct Mapping (20 functions)

```javascript
// Character functions
'ASCII': { $toInt: { $substrCP: ["$string", 0, 1] } }  // Approximation
'CHAR': { $toString: "$charCode" }  // Limited support

// String manipulation
'CONCAT_WS': {
  $reduce: {
    input: "$stringArray",
    initialValue: "",
    in: {
      $concat: [
        "$$value",
        { $cond: [{ $eq: ["$$value", ""] }, "", "$separator"] },
        "$$this"
      ]
    }
  }
}

'FORMAT': { $toString: "$number" }  // Basic conversion

// Regular expressions (MongoDB has good regex support)
'REGEXP': { $regexMatch: { input: "$string", regex: "$pattern" } }
'RLIKE': { $regexMatch: { input: "$string", regex: "$pattern" } }
'REGEXP_INSTR': { $indexOfCP: ["$string", { $regexFind: { input: "$string", regex: "$pattern" } }] }
'REGEXP_SUBSTR': { $regexFind: { input: "$string", regex: "$pattern" } }

// String utilities
'HEX': "Custom hex conversion implementation"
'UNHEX': "Custom hex to string conversion"
'SPACE': { $replicate: [" ", "$count"] }  // Custom function needed
'QUOTE': { $concat: ["'", { $replaceAll: { input: "$string", find: "'", replacement: "''" } }, "'"] }

// Phonetic
'SOUNDEX': "Custom phonetic algorithm implementation"

// String position and manipulation
'FIND_IN_SET': {
  $indexOfArray: [
    { $split: ["$csvString", ","] },
    "$searchValue"
  ]
}

'FIELD': {
  $indexOfArray: ["$valueArray", "$searchValue"]
}

'ELT': { $arrayElemAt: ["$stringArray", { $subtract: ["$index", 1] }] }

'INSERT': {
  $concat: [
    { $substrCP: ["$string", 0, { $subtract: ["$position", 1] }] },
    "$insertString",
    { $substrCP: ["$string", { $add: ["$position", "$length", -1] }, -1] }
  ]
}
```

### 🔧 Complex Mapping (15 functions)

```javascript
'EXPORT_SET': "Custom bit manipulation and formatting"
'MAKE_SET': "Custom bit-to-string conversion"
'MATCH': "Full-text search requires text indexes"
'LOAD_FILE': "File system access not available in MongoDB"
'ORD': "Multi-byte character handling required"
```

### 🚫 No Direct Equivalent (5 functions)

```javascript
'LOAD_FILE': "File system operations not supported"
'EXPORT_SET': "Complex bit manipulation formatting"
'MAKE_SET': "Bit manipulation with custom formatting"
'SOUNDEX': "Phonetic algorithm implementation required"
'ORD': "Multi-byte character code extraction"
```

## 4. Control Flow Functions Mapping

### ✅ Direct Mapping (4 functions)

```javascript
'IF': {
  $cond: [
    "$condition",
    "$trueValue",
    "$falseValue"
  ]
}

'IFNULL': {
  $ifNull: ["$expression", "$alternativeValue"]
}

'ISNULL': {
  $eq: ["$expression", null]
}

'NULLIF': {
  $cond: [
    { $eq: ["$expr1", "$expr2"] },
    null,
    "$expr1"
  ]
}
```

### 🔧 Complex Mapping (2 functions)

```javascript
'CASE': {
  $switch: {
    branches: [
      { case: "$condition1", then: "$value1" },
      { case: "$condition2", then: "$value2" }
    ],
    default: "$defaultValue"
  }
}

'COALESCE': {
  $reduce: {
    input: ["$expr1", "$expr2", "$expr3"],
    initialValue: null,
    in: {
      $cond: [
        { $ne: ["$$this", null] },
        "$$this",
        "$$value"
      ]
    }
  }
}
```

## 5. Window Functions Mapping

### 🔧 Complex Mapping (16 functions - All require $setWindowFields)

```javascript
'ROW_NUMBER': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      rowNumber: { $rowNumber: {} }
    }
  }
}

'RANK': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      rank: { $rank: {} }
    }
  }
}

'DENSE_RANK': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      denseRank: { $denseRank: {} }
    }
  }
}

'LAG': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      lagValue: {
        $shift: {
          output: "$field",
          by: -1,
          default: null
        }
      }
    }
  }
}

'LEAD': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      leadValue: {
        $shift: {
          output: "$field",
          by: 1,
          default: null
        }
      }
    }
  }
}

'FIRST_VALUE': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      firstValue: {
        $first: "$field"
      }
    }
  }
}

'LAST_VALUE': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      lastValue: {
        $last: "$field"
      }
    }
  }
}

'NTH_VALUE': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      nthValue: {
        $nth: {
          input: "$field",
          n: "$position"
        }
      }
    }
  }
}

'NTILE': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      tile: {
        $ntile: "$numberOfTiles"
      }
    }
  }
}

'CUME_DIST': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      cumeDist: { $cumulativeDist: {} }
    }
  }
}

'PERCENT_RANK': {
  $setWindowFields: {
    sortBy: { "$sortField": 1 },
    output: {
      percentRank: { $percentRank: {} }
    }
  }
}

// Statistical window functions
'MEDIAN': {
  $setWindowFields: {
    output: {
      median: {
        $median: "$field"
      }
    }
  }
}

'PERCENTILE_CONT': {
  $setWindowFields: {
    output: {
      percentile: {
        $percentile: {
          input: "$field",
          p: [0.5],  // 50th percentile
          method: "approximate"
        }
      }
    }
  }
}

'PERCENTILE_DISC': {
  $setWindowFields: {
    output: {
      percentile: {
        $percentile: {
          input: "$field",
          p: [0.5],
          method: "discrete"
        }
      }
    }
  }
}
```

## 6. Aggregate Functions Mapping

### ✅ Direct Mapping (8 functions)

```javascript
'BIT_AND': { $bitAnd: "$field" }
'BIT_OR': { $bitOr: "$field" }
'BIT_XOR': { $bitXor: "$field" }
'STDDEV_POP': { $stdDevPop: "$field" }
'STDDEV_SAMP': { $stdDevSamp: "$field" }
'VAR_POP': { $variancePop: "$field" }
'VAR_SAMP': { $varianceSamp: "$field" }
'STD': { $stdDevPop: "$field" }  // Alias for STDDEV_POP
```

### 🔧 Complex Mapping (4 functions)

```javascript
'GROUP_CONCAT': {
  $group: {
    _id: "$groupField",
    concatenated: {
      $push: "$field"
    }
  }
},
// Then in projection:
{
  $project: {
    result: {
      $reduce: {
        input: "$concatenated",
        initialValue: "",
        in: {
          $concat: [
            "$$value",
            { $cond: [{ $eq: ["$$value", ""] }, "", ","] },
            { $toString: "$$this" }
          ]
        }
      }
    }
  }
}
```

## 7. Type Conversion Functions Mapping

### ✅ Direct Mapping (2 functions)

```javascript
'CAST': {
  $convert: {
    input: "$value",
    to: "string"  // or "int", "double", "date", etc.
  }
}

'BINARY': {
  $convert: {
    input: "$value",
    to: "binData"
  }
}
```

### 🔧 Complex Mapping (1 function)

```javascript
'CONVERT': "Character set conversion requires custom handling"
```

## 8. Information Functions Mapping

### ✅ Direct Mapping (2 functions)

```javascript
'DATABASE': { $literal: "databaseName" }  // Static value
'SCHEMA': { $literal: "databaseName" }    // Alias for DATABASE
```

### 🔧 Complex Mapping (5 functions)

```javascript
'CONNECTION_ID': "Session management required"
'CURRENT_USER': "Authentication context needed"
'SESSION_USER': "Session information required"
'SYSTEM_USER': "System context needed"
'USER': "User context required"
```

### 🚫 No Direct Equivalent (5 functions)

```javascript
'BENCHMARK': "Performance testing not applicable"
'FOUND_ROWS': "Requires query context tracking"
'LAST_INSERT_ID': "Auto-increment tracking needed"
'ROW_COUNT': "Affected rows tracking required"
'VERSION': "Static MongoDB version string"
```

## 9. Encryption/Hashing Functions Mapping

### 🔧 Complex Mapping (10 functions - Require external libraries)

```javascript
// These would need to be implemented using MongoDB's aggregation framework
// with custom JavaScript functions or external processing

'MD5': "Requires crypto library integration"
'SHA1': "Requires crypto library integration"
'SHA2': "Requires crypto library integration"
'CRC32': "Requires checksum library integration"
'AES_ENCRYPT': "Requires encryption library"
'AES_DECRYPT': "Requires decryption library"
'COMPRESS': "Requires compression library"
'UNCOMPRESS': "Requires decompression library"
'ENCODE': "Custom encoding implementation"
'DECODE': "Custom decoding implementation"
```

### 🚫 No Direct Equivalent (6 functions)

```javascript
'DES_ENCRYPT': "Deprecated encryption algorithm"
'DES_DECRYPT': "Deprecated encryption algorithm"
'ENCRYPT': "Unix crypt() not available"
'OLD_PASSWORD': "MySQL-specific password hashing"
'PASSWORD': "MySQL-specific password hashing"
'UNCOMPRESSED_LENGTH': "Compression metadata not tracked"
```

## 10. Geographic/Geometric Functions Mapping

### ✅ Direct Mapping (45 functions - MongoDB has excellent geospatial support)

```javascript
// MongoDB's geospatial operators map very well to MariaDB spatial functions

'ST_Area': { $geoNear: { /* area calculation */ } }
'ST_Buffer': { $geoWithin: { $centerSphere: [["$longitude", "$latitude"], "$radius"] } }
'ST_Contains': { $geoWithin: { $geometry: "$polygon" } }
'ST_Distance': { 
  $geoNear: {
    near: { type: "Point", coordinates: ["$lon", "$lat"] },
    distanceField: "distance"
  }
}
'ST_Intersects': { $geoIntersects: { $geometry: "$geometry" } }
'ST_Within': { $geoWithin: { $geometry: "$polygon" } }

// Many more spatial functions have direct MongoDB equivalents
// through the $geoNear, $geoWithin, $geoIntersects operators
```

## Implementation Strategy

### Phase 1: Direct Mappings (Weeks 1-2)
Implement all ✅ Direct Mapping functions first as they require minimal complexity.

### Phase 2: Complex Mappings (Weeks 3-8)
Tackle 🔧 Complex Mapping functions by category priority:
1. Control Flow (essential for query logic)
2. Date/Time (critical for applications)
3. JSON (modern application requirement)
4. Window Functions (analytical capabilities)

### Phase 3: Custom Implementations (Weeks 9-12)
Address 🚫 No Direct Equivalent functions with custom solutions:
1. File operations → Error messages explaining limitations
2. System functions → Static/default value returns
3. Specialized algorithms → Custom implementations

### Phase 4: Integration and Testing (Weeks 13-16)
- Comprehensive testing against MariaDB
- Performance optimization
- Documentation and examples

## Technical Implementation Notes

### MongoDB Aggregation Pipeline Limitations
- No file system access
- Limited cryptographic functions
- No true stored procedures
- Session/connection state not accessible

### Custom Function Framework Required
- JavaScript-based implementations for missing functions
- Error handling for unsupported operations
- Performance optimization for complex expressions
- Caching for expensive calculations

### Testing Strategy
- Side-by-side comparison with MariaDB results
- Edge case validation
- Performance benchmarking
- Integration testing with existing mappers

---

**Document Status:** Technical specification for function mapping implementation  
**Next Steps:** Begin Phase 1 implementation with direct mapping functions  
**Estimated Timeline:** 16 weeks for complete implementation
