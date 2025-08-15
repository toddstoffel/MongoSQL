# Copilot Development Reminders

## CRITICAL - READ FIRST EVERY TIME

### 1. NO REGEX PARSING - USE TOKENS ONLY
- **NEVER** use regex (`import re`, `re.match`, `re.search`, etc.) for SQL parsing
- **ALWAYS** use sqlparse tokens for all SQL parsing operations
- Token-based parsing is more reliable, handles edge cases, and follows project architecture
- If you see regex in existing code, replace it with token-based parsing

### 2. ENVIRONMENT SETUP
- **ALWAYS** check and use the `.env` file for MongoDB connection settings
- **NEVER** use hardcoded localhost values
- Load environment variables with `load_dotenv()` before connecting
- Check `.env` file contents before making any MongoDB connections

### 3. MONGODB CONNECTION
- MongoDB connection details are in `.env` file
- Use `MongoDBClient(host=os.getenv('MONGO_HOST'), username=os.getenv('MONGO_USERNAME'), password=os.getenv('MONGO_PASSWORD'), database='classicmodels')`
- Always call `load_dotenv()` first
- Check if MongoDB is running if connection fails

### 4. FILE EDITING BEST PRACTICES
- **ALWAYS** include 3-5 lines of context before and after when using `replace_string_in_file`
- Read the file first to understand the exact context
- Never use placeholder comments like `...existing code...`
- Match whitespace and indentation exactly

### 5. TESTING WORKFLOW
1. Check `.env` file exists and has correct MongoDB settings
2. Load environment variables with `load_dotenv()`
3. Test parsing → translation → execution pipeline step by step
4. Use proper connection parameters from environment

### 6. COMMON MISTAKES TO AVOID
- ❌ Using regex for SQL parsing (use sqlparse tokens instead)
- ❌ Using localhost hardcoded values
- ❌ Not loading .env file
- ❌ Not including enough context in file edits
- ❌ Assuming MongoDB is running without checking
- ❌ Not reading the full error message carefully

### 7. DEBUGGING PROCESS
1. First check `.env` file
2. Load environment variables
3. Test each component separately (parser → translator → database)
4. Check actual error messages, don't assume

### 8. CURRENT PROJECT STATUS
- MongoSQL translator with 89.6% MariaDB compatibility
- GROUP BY module fully implemented and working (100% success)
- All major modules complete: ORDER BY, JOINs, GROUP BY
- Issue: Some regex usage still exists - replace with token-based parsing

## BEFORE EVERY DEBUGGING SESSION:
1. ✅ Check `.env` file contents
2. ✅ Load environment variables
3. ✅ Verify MongoDB connection works
4. ✅ Test step by step pipeline
5. ✅ Use token-based parsing only (NO REGEX)