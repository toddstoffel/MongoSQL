"""
Master function mapper that coordinates between specialized function mappers
This is the main entry point for all SQL to MongoDB function mappings
"""
from typing import Dict, List, Any, Optional
from .aggregate_functions import AggregateFunctionMapper
from .string_functions import StringFunctionMapper
from .math_functions import MathFunctionMapper
from .datetime_functions import DateTimeFunctionMapper
from ..modules.conditional.conditional_function_mapper import ConditionalFunctionMapper
from ..modules.json.json_function_mapper import JSONFunctionMapper
from ..modules.extended_string.extended_string_function_mapper import ExtendedStringFunctionMapper
from ..modules.regexp.regexp_function_mapper import RegexpFunctionMapper
from ..modules.enhanced_aggregate.enhanced_aggregate_function_mapper import EnhancedAggregateFunctionMapper

class FunctionMapper:
    """Master mapper that delegates to specialized function mappers"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern for function mapper caching"""
        if cls._instance is None:
            cls._instance = super(FunctionMapper, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if FunctionMapper._initialized:
            return
            
        # Initialize specialized mappers
        self.aggregate_mapper = AggregateFunctionMapper()
        self.string_mapper = StringFunctionMapper()
        self.math_mapper = MathFunctionMapper()
        self.datetime_mapper = DateTimeFunctionMapper()
        self.conditional_mapper = ConditionalFunctionMapper()
        self.json_mapper = JSONFunctionMapper()
        self.extended_string_mapper = ExtendedStringFunctionMapper()
        self.regexp_mapper = RegexpFunctionMapper()
        self.enhanced_aggregate_mapper = EnhancedAggregateFunctionMapper()
        
        # Cache for function categorization
        self._function_categories = self._build_function_categories()
        
        FunctionMapper._initialized = True
    
    def _build_function_categories(self) -> Dict[str, str]:
        """Build a mapping of function names to their categories"""
        categories = {}
        
        # Enhanced aggregate functions (priority over basic aggregates)
        for func in self.enhanced_aggregate_mapper.get_supported_functions():
            categories[func.upper()] = 'enhanced_aggregate'
        
        # Aggregate functions
        for func in self.aggregate_mapper.get_supported_functions():
            # Only add if not already in enhanced_aggregate category
            if func.upper() not in categories:
                categories[func.upper()] = 'aggregate'
        
        # String functions
        for func in self.string_mapper.get_supported_functions():
            categories[func.upper()] = 'string'
        
        # Math functions
        for func in self.math_mapper.get_supported_functions():
            categories[func.upper()] = 'math'
        
        # Date/Time functions
        for func in self.datetime_mapper.function_map.keys():
            categories[func.upper()] = 'datetime'
        
        # Conditional functions
        for func in self.conditional_mapper.get_supported_functions():
            categories[func.upper()] = 'conditional'
        
        # JSON functions
        for func in self.json_mapper.get_supported_functions():
            categories[func.upper()] = 'json'
        
        # Extended string functions
        for func in self.extended_string_mapper.get_supported_functions():
            categories[func.upper()] = 'extended_string'
        
        return categories
    
    def map_function(self, function_name: str, args: List[Any] = None, context: str = None) -> Dict[str, Any]:
        """Map SQL function to MongoDB equivalent using appropriate specialized mapper"""
        func_upper = function_name.upper()
        
        # Determine function category
        category = self._function_categories.get(func_upper)
        
        if not category:
            raise ValueError(f"Unsupported function: {function_name}")
        
        try:
            if category == 'enhanced_aggregate':
                # Enhanced aggregate functions with complex syntax support
                return self.enhanced_aggregate_mapper.map_enhanced_aggregate_function(function_name, str(args) if args else '', f"{function_name}({', '.join(str(arg) for arg in args) if args else ''})")
            
            elif category == 'aggregate':
                # For aggregate functions, we might need field information
                if args and len(args) > 0:
                    field = args[0] if args[0] != '*' else None
                    return self.aggregate_mapper.map_function(function_name, field, args)
                else:
                    return self.aggregate_mapper.map_function(function_name, None, args)
            
            elif category == 'string':
                return self.string_mapper.map_function(function_name, args)
            
            elif category == 'math':
                return self.math_mapper.map_function(function_name, args)
            
            elif category == 'datetime':
                return self.datetime_mapper.map_function(function_name, args)
            
            elif category == 'conditional':
                return self.conditional_mapper.map_function(function_name, args)
            
            elif category == 'json':
                return self.json_mapper.map_json_function(function_name, args)
            
            elif category == 'extended_string':
                return self.extended_string_mapper.map_extended_string_function(function_name, args)
            
            else:
                raise ValueError(f"Unknown function category: {category}")
                
        except Exception as e:
            raise ValueError(f"Error mapping function {function_name}: {str(e)}")
    
    def get_function_category(self, function_name: str) -> Optional[str]:
        """Get the category of a function"""
        return self._function_categories.get(function_name.upper())
    
    def is_aggregate_function(self, function_name: str) -> bool:
        """Check if function is an aggregate function (including enhanced aggregates)"""
        return (self.enhanced_aggregate_mapper.is_supported_enhanced_aggregate(function_name) or 
                self.aggregate_mapper.is_aggregate_function(function_name))
    
    def is_string_function(self, function_name: str) -> bool:
        """Check if function is a string function"""
        return self.string_mapper.is_string_function(function_name)
    
    def is_math_function(self, function_name: str) -> bool:
        """Check if function is a mathematical function"""
        return self.math_mapper.is_math_function(function_name)
    
    def is_datetime_function(self, function_name: str) -> bool:
        """Check if function is a date/time function"""
        return self.datetime_mapper.is_datetime_function(function_name)
    
    def is_conditional_function(self, function_name: str) -> bool:
        """Check if function is a conditional function"""
        return self.conditional_mapper.is_conditional_function(function_name)
    
    def is_enhanced_aggregate_function(self, function_name: str) -> bool:
        """Check if function is an enhanced aggregate function"""
        return self.enhanced_aggregate_mapper.is_supported_enhanced_aggregate(function_name)
    
    def is_json_function(self, function_name: str) -> bool:
        """Check if function is a JSON function"""
        return self.json_mapper.is_json_function(function_name)
    
    def is_extended_string_function(self, function_name: str) -> bool:
        """Check if function is an extended string function"""
        return self.extended_string_mapper.is_extended_string_function(function_name)
    
    def is_regexp_expression(self, expression: str) -> bool:
        """Check if expression contains REGEXP operators"""
        return self.regexp_mapper.has_regexp_expressions(expression)
    
    def map_regexp_expression(self, expression: str, context: str = 'SELECT', alias: str = None) -> Optional[Dict[str, Any]]:
        """Map REGEXP expressions to MongoDB expressions"""
        return self.regexp_mapper.translate_infix_regexp(expression, context, alias)
    
    def get_all_supported_functions(self) -> Dict[str, List[str]]:
        """Get all supported functions organized by category"""
        return {
            'enhanced_aggregate': self.enhanced_aggregate_mapper.get_supported_functions(),
            'aggregate': self.aggregate_mapper.get_supported_functions(),
            'string': self.string_mapper.get_supported_functions(),
            'math': self.math_mapper.get_supported_functions(),
            'datetime': list(self.datetime_mapper.function_map.keys()),
            'conditional': self.conditional_mapper.get_supported_functions(),
            'json': self.json_mapper.get_supported_functions(),
            'extended_string': self.extended_string_mapper.get_supported_functions()
        }
    
    def get_function_info(self, function_name: str) -> Dict[str, Any]:
        """Get detailed information about a function"""
        func_upper = function_name.upper()
        category = self._function_categories.get(func_upper)
        
        if not category:
            return {'supported': False}
        
        info = {'supported': True, 'category': category}
        
        try:
            if category == 'enhanced_aggregate':
                mapper_info = {'description': f'Enhanced aggregate function: {function_name}', 'mongodb': 'enhanced_pipeline'}
            elif category == 'aggregate':
                mapper_info = self.aggregate_mapper.function_map.get(func_upper, {})
            elif category == 'string':
                mapper_info = self.string_mapper.function_map.get(func_upper, {})
            elif category == 'math':
                mapper_info = self.math_mapper.function_map.get(func_upper, {})
            elif category == 'datetime':
                mapper_info = self.datetime_mapper.function_map.get(func_upper, {})
            elif category == 'conditional':
                mapper_info = self.conditional_mapper.get_function_info(func_upper) or {}
            else:
                mapper_info = {}
            
            info.update(mapper_info)
            
        except Exception:
            pass
        
        return info
