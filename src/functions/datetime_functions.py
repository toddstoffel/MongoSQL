"""
Date/Time function mappers for SQL to MongoDB conversion.
Maps MariaDB/MySQL date/time functions to MongoDB aggregation pipeline expressions.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional


class DateTimeFunctionMapper:
    """Maps SQL date/time functions to MongoDB aggregation expressions."""
    
    def __init__(self):
        # Map function names to their handlers
        self.function_map = {
            # Current date/time functions
            'NOW': self._map_now,
            'CURDATE': self._map_curdate,
            'CURTIME': self._map_curtime,
            'CURRENT_DATE': self._map_current_date,
            'CURRENT_TIME': self._map_current_time,
            'CURRENT_TIMESTAMP': self._map_current_timestamp,
            'LOCALTIME': self._map_localtime,
            'LOCALTIMESTAMP': self._map_localtimestamp,
            'SYSDATE': self._map_sysdate,
            'UTC_DATE': self._map_utc_date,
            'UTC_TIME': self._map_utc_time,
            'UTC_TIMESTAMP': self._map_utc_timestamp,
            
            # Date extraction functions
            'YEAR': self._map_year,
            'MONTH': self._map_month,
            'DAY': self._map_day,
            'DAYOFMONTH': self._map_dayofmonth,
            'DAYOFWEEK': self._map_dayofweek,
            'DAYOFYEAR': self._map_dayofyear,
            'WEEKDAY': self._map_weekday,
            'WEEK': self._map_week,
            'WEEKOFYEAR': self._map_weekofyear,
            'YEARWEEK': self._map_yearweek,
            'MONTHNAME': self._map_monthname,
            'QUARTER': self._map_quarter,
            'HOUR': self._map_hour,
            'MINUTE': self._map_minute,
            'SECOND': self._map_second,
            'MICROSECOND': self._map_microsecond,
            
            # Date formatting functions
            'DATE_FORMAT': self._map_date_format,
            'TIME_FORMAT': self._map_time_format,
            'STR_TO_DATE': self._map_str_to_date,
            'DATE': self._map_date,
            'TIME': self._map_time,
            'CONVERT_TZ': self._map_convert_tz,
            
            # Date arithmetic functions
            'DATE_ADD': self._map_date_add,
            'DATE_SUB': self._map_date_sub,
            'ADDDATE': self._map_adddate,
            'SUBDATE': self._map_subdate,
            'ADDTIME': self._map_addtime,
            'DATEDIFF': self._map_datediff,
            'TIMEDIFF': self._map_timediff,
            'TIMESTAMPDIFF': self._map_timestampdiff,
            'TIMESTAMPADD': self._map_timestampadd,
            'EXTRACT': self._map_extract,
            
            # Date utility functions
            'DAYNAME': self._map_dayname,
            'MONTHNAME': self._map_monthname,
            'LAST_DAY': self._map_last_day,
            'MAKEDATE': self._map_makedate,
            'MAKETIME': self._map_maketime,
            'UNIX_TIMESTAMP': self._map_unix_timestamp,
            'FROM_UNIXTIME': self._map_from_unixtime,
            'FROM_DAYS': self._map_from_days,
            'TO_DAYS': self._map_to_days,
            'SEC_TO_TIME': self._map_sec_to_time,
            'TIME_TO_SEC': self._map_time_to_sec,
            'SUBTIME': self._map_subtime,
            'PERIOD_ADD': self._map_period_add,
            'PERIOD_DIFF': self._map_period_diff,
        }
    
    def map_function(self, function_name: str, args: List[Any]) -> Optional[Dict[str, Any]]:
        """
        Map a SQL date/time function to MongoDB aggregation expression.
        
        Args:
            function_name: Name of the SQL function (case-insensitive)
            args: List of function arguments
            
        Returns:
            MongoDB aggregation expression or None if function not supported
        """
        func_upper = function_name.upper()
        
        # Special handling for EXTRACT(unit FROM date) syntax
        if func_upper == 'EXTRACT' and len(args) == 1:
            # Parse "unit FROM date" format
            arg_str = str(args[0])
            if ' FROM ' in arg_str.upper():
                parts = arg_str.split(' FROM ', 1)
                if len(parts) == 2:
                    unit = parts[0].strip().strip("'\"")
                    date_expr = parts[1].strip().strip("'\"")
                    return self._map_extract([unit, date_expr])
        
        if func_upper in self.function_map:
            return self.function_map[func_upper](args)
        return None
    
    def is_datetime_function(self, function_name: str) -> bool:
        """Check if a function is a date/time function."""
        return function_name.upper() in self.function_map
    
    # Current date/time function mappings
    def _map_now(self, args: List[Any]) -> Dict[str, Any]:
        """NOW() -> $$NOW"""
        return {"$dateToString": {"date": "$$NOW", "format": "%Y-%m-%d %H:%M:%S"}}
    
    def _map_curdate(self, args: List[Any]) -> Dict[str, Any]:
        """CURDATE() -> current date"""
        return {"$dateToString": {"date": "$$NOW", "format": "%Y-%m-%d"}}
    
    def _map_curtime(self, args: List[Any]) -> Dict[str, Any]:
        """CURTIME() -> current time"""
        return {"$dateToString": {"date": "$$NOW", "format": "%H:%M:%S"}}
    
    def _map_current_date(self, args: List[Any]) -> Dict[str, Any]:
        """CURRENT_DATE -> current date"""
        return self._map_curdate(args)
    
    def _map_current_time(self, args: List[Any]) -> Dict[str, Any]:
        """CURRENT_TIME -> current time"""
        return self._map_curtime(args)
    
    def _map_current_timestamp(self, args: List[Any]) -> Dict[str, Any]:
        """CURRENT_TIMESTAMP -> current timestamp"""
        return self._map_now(args)
    
    def _map_localtime(self, args: List[Any]) -> Dict[str, Any]:
        """LOCALTIME -> current timestamp"""
        return self._map_now(args)
    
    def _map_localtimestamp(self, args: List[Any]) -> Dict[str, Any]:
        """LOCALTIMESTAMP -> current timestamp"""
        return self._map_now(args)
    
    def _map_sysdate(self, args: List[Any]) -> Dict[str, Any]:
        """SYSDATE() -> current timestamp"""
        return self._map_now(args)
    
    def _map_utc_date(self, args: List[Any]) -> Dict[str, Any]:
        """UTC_DATE() -> current UTC date"""
        return {"$dateToString": {"date": "$$NOW", "format": "%Y-%m-%d", "timezone": "UTC"}}
    
    def _map_utc_time(self, args: List[Any]) -> Dict[str, Any]:
        """UTC_TIME() -> current UTC time"""
        return {"$dateToString": {"date": "$$NOW", "format": "%H:%M:%S", "timezone": "UTC"}}
    
    def _map_utc_timestamp(self, args: List[Any]) -> Dict[str, Any]:
        """UTC_TIMESTAMP() -> current UTC timestamp"""
        return {"$dateToString": {"date": "$$NOW", "format": "%Y-%m-%d %H:%M:%S", "timezone": "UTC"}}
    
    # Date extraction function mappings
    def _map_year(self, args: List[Any]) -> Dict[str, Any]:
        """YEAR(date) -> extract year"""
        if not args:
            return {"$year": "$$NOW"}
        date_expr = self._convert_date_arg(args[0])
        return {"$year": date_expr}
    
    def _map_month(self, args: List[Any]) -> Dict[str, Any]:
        """MONTH(date) -> extract month"""
        if not args:
            return {"$month": "$$NOW"}
        date_expr = self._convert_date_arg(args[0])
        return {"$month": date_expr}
    
    def _map_day(self, args: List[Any]) -> Dict[str, Any]:
        """DAY(date) -> extract day"""
        return self._map_dayofmonth(args)
    
    def _map_dayofmonth(self, args: List[Any]) -> Dict[str, Any]:
        """DAYOFMONTH(date) -> extract day of month"""
        if not args:
            return {"$dayOfMonth": "$$NOW"}
        date_expr = self._convert_date_arg(args[0])
        return {"$dayOfMonth": date_expr}
    
    def _map_dayofweek(self, args: List[Any]) -> Dict[str, Any]:
        """DAYOFWEEK(date) -> extract day of week (1=Sunday)"""
        if not args:
            return {"$dayOfWeek": "$$NOW"}
        date_expr = self._convert_date_arg(args[0])
        return {"$dayOfWeek": date_expr}
    
    def _map_dayofyear(self, args: List[Any]) -> Dict[str, Any]:
        """DAYOFYEAR(date) -> extract day of year"""
        if not args:
            return {"$dayOfYear": "$$NOW"}
        date_expr = self._convert_date_arg(args[0])
        return {"$dayOfYear": date_expr}
    
    def _map_weekday(self, args: List[Any]) -> Dict[str, Any]:
        """WEEKDAY(date) -> extract weekday (0=Monday)"""
        if not args:
            base_expr = {"$dayOfWeek": "$$NOW"}
        else:
            date_expr = self._convert_date_arg(args[0])
            base_expr = {"$dayOfWeek": date_expr}
        
        # Convert from MongoDB's 1=Sunday to MySQL's 0=Monday and ensure integer result
        return {"$toInt": {"$subtract": [{"$subtract": [base_expr, 2]}, {"$multiply": [{"$floor": {"$divide": [{"$subtract": [base_expr, 2]}, 7]}}, 7]}]}}
    
    def _map_week(self, args: List[Any]) -> Dict[str, Any]:
        """WEEK(date) -> extract week"""
        if not args:
            return {"$week": "$$NOW"}
        date_expr = self._convert_date_arg(args[0])
        return {"$week": date_expr}
    
    def _map_weekofyear(self, args: List[Any]) -> Dict[str, Any]:
        """WEEKOFYEAR(date) -> extract week of year (MariaDB mode 3: Monday start, first week has >=4 days)"""
        if not args:
            date_expr = "$$NOW"
        else:
            date_expr = self._convert_date_arg(args[0])
        
        # MariaDB WEEKOFYEAR uses mode 3: Monday=1, first week must have >=4 days
        # MongoDB $isoWeek is closest to this behavior
        return {"$isoWeek": date_expr}
    
    def _map_yearweek(self, args: List[Any]) -> Dict[str, Any]:
        """YEARWEEK(date) -> extract year and week"""
        if not args:
            date_expr = "$$NOW"
        else:
            date_expr = self._convert_date_arg(args[0])
        
        return {
            "$add": [
                {"$multiply": [{"$year": date_expr}, 100]},
                {"$week": date_expr}
            ]
        }
    
    def _map_monthname(self, args: List[Any]) -> Dict[str, Any]:
        """MONTHNAME(date) -> full month name"""
        if not args:
            date_expr = "$$NOW"
        else:
            date_expr = self._convert_date_arg(args[0])
        
        return {"$dateToString": {"date": date_expr, "format": "%B"}}
    
    def _map_dayname(self, args: List[Any]) -> Dict[str, Any]:
        """DAYNAME(date) -> full day name"""
        if not args:
            date_expr = "$$NOW"
        else:
            date_expr = self._convert_date_arg(args[0])
        
        # Use $switch to convert dayOfWeek (1=Sunday) to day names
        # MongoDB $dayOfWeek returns 1=Sunday, 2=Monday, etc.
        return {
            "$switch": {
                "branches": [
                    {"case": {"$eq": [{"$dayOfWeek": date_expr}, 1]}, "then": "Sunday"},
                    {"case": {"$eq": [{"$dayOfWeek": date_expr}, 2]}, "then": "Monday"},
                    {"case": {"$eq": [{"$dayOfWeek": date_expr}, 3]}, "then": "Tuesday"},
                    {"case": {"$eq": [{"$dayOfWeek": date_expr}, 4]}, "then": "Wednesday"},
                    {"case": {"$eq": [{"$dayOfWeek": date_expr}, 5]}, "then": "Thursday"},
                    {"case": {"$eq": [{"$dayOfWeek": date_expr}, 6]}, "then": "Friday"},
                    {"case": {"$eq": [{"$dayOfWeek": date_expr}, 7]}, "then": "Saturday"}
                ],
                "default": "Unknown"
            }
        }
    
    def _map_quarter(self, args: List[Any]) -> Dict[str, Any]:
        """QUARTER(date) -> extract quarter"""
        if not args:
            month_expr = {"$month": "$$NOW"}
        else:
            date_expr = self._convert_date_arg(args[0])
            month_expr = {"$month": date_expr}
        
        return {"$toInt": {"$ceil": {"$divide": [month_expr, 3]}}}
    
    def _map_hour(self, args: List[Any]) -> Dict[str, Any]:
        """HOUR(time) -> extract hour"""
        if not args:
            return {"$hour": "$$NOW"}
        
        date_expr = self._convert_date_arg(args[0])
        
        # Handle time-only strings like '14:30:45'
        if isinstance(args[0], str):
            time_str = args[0].strip("'\"")
            if ':' in time_str and len(time_str.split(':')) >= 2:
                # This is a time-only string, convert to full datetime
                date_expr = {
                    "$dateFromString": {
                        "dateString": f"1970-01-01T{time_str}"
                    }
                }
        
        return {"$hour": date_expr}
    
    def _map_minute(self, args: List[Any]) -> Dict[str, Any]:
        """MINUTE(time) -> extract minute"""
        if not args:
            return {"$minute": "$$NOW"}
        
        date_expr = self._convert_date_arg(args[0])
        
        # Handle time-only strings like '14:30:45'
        if isinstance(args[0], str):
            time_str = args[0].strip("'\"")
            if ':' in time_str and len(time_str.split(':')) >= 2:
                # This is a time-only string, convert to full datetime
                date_expr = {
                    "$dateFromString": {
                        "dateString": f"1970-01-01T{time_str}"
                    }
                }
        
        return {"$minute": date_expr}
    
    def _map_second(self, args: List[Any]) -> Dict[str, Any]:
        """SECOND(time) -> extract second"""
        if not args:
            return {"$second": "$$NOW"}
        
        date_expr = self._convert_date_arg(args[0])
        
        # Handle time-only strings like '14:30:45'
        if isinstance(args[0], str):
            time_str = args[0].strip("'\"")
            if ':' in time_str and len(time_str.split(':')) >= 2:
                # This is a time-only string, convert to full datetime
                date_expr = {
                    "$dateFromString": {
                        "dateString": f"1970-01-01T{time_str}"
                    }
                }
        
        return {"$second": date_expr}
    
    def _map_microsecond(self, args: List[Any]) -> Dict[str, Any]:
        """MICROSECOND(time) -> extract microsecond"""
        if not args:
            return {"$millisecond": "$$NOW"}
        date_expr = self._convert_date_arg(args[0])
        return {"$multiply": [{"$millisecond": date_expr}, 1000]}
    
    # Placeholder mappings for complex functions
    def _map_date_format(self, args: List[Any]) -> Dict[str, Any]:
        """DATE_FORMAT(date, format) -> format date"""
        if len(args) < 2:
            return {"$literal": "DATE_FORMAT requires 2 arguments"}
        
        date_expr = self._convert_date_arg(args[0])
        format_str = str(args[1]).strip("'\"")
        
        # Convert MySQL format to MongoDB format
        mongo_format = self._convert_date_format(format_str)
        return {"$dateToString": {"date": date_expr, "format": mongo_format}}
    
    def _map_time_format(self, args: List[Any]) -> Dict[str, Any]:
        """TIME_FORMAT(time, format) -> format time"""
        return self._map_date_format(args)
    
    def _map_convert_tz(self, args: List[Any]) -> Dict[str, Any]:
        """CONVERT_TZ(dt, from_tz, to_tz) -> convert between time zones"""
        if len(args) < 3:
            return {"$literal": "CONVERT_TZ requires 3 arguments: datetime, from_tz, to_tz"}
        
        date_expr = self._convert_date_arg(args[0])
        from_tz = str(args[1]).strip("'\"")
        to_tz = str(args[2]).strip("'\"")
        
        # Convert timezone names to MongoDB format
        from_tz_mongo = self._convert_timezone(from_tz)
        to_tz_mongo = self._convert_timezone(to_tz)
        
        # Correct MongoDB approach: interpret the datetime in from_tz, then convert to to_tz
        return {
            "$dateToString": {
                "date": {
                    "$dateFromString": {
                        "dateString": {
                            "$dateToString": {
                                "date": date_expr,
                                "format": "%Y-%m-%dT%H:%M:%S",
                                "timezone": "UTC"  # Treat input as UTC first
                            }
                        },
                        "timezone": from_tz_mongo  # Then interpret in from timezone
                    }
                },
                "format": "%Y-%m-%d %H:%M:%S",
                "timezone": to_tz_mongo  # Finally convert to target timezone
            }
        }
    
    def _map_str_to_date(self, args: List[Any]) -> Dict[str, Any]:
        """STR_TO_DATE(str, format) -> parse date string"""
        if len(args) < 2:
            return {"$literal": "STR_TO_DATE requires 2 arguments"}
        
        date_str = str(args[0]).strip("'\"")
        format_str = str(args[1]).strip("'\"")
        
        # Basic implementation - MongoDB has limited date parsing
        return {"$dateFromString": {"dateString": date_str}}
    
    def _map_date(self, args: List[Any]) -> Dict[str, Any]:
        """DATE(datetime) -> extract date part"""
        if not args:
            return {"$dateToString": {"date": "$$NOW", "format": "%Y-%m-%d"}}
        
        date_expr = self._convert_date_arg(args[0])
        return {"$dateToString": {"date": date_expr, "format": "%Y-%m-%d"}}
    
    def _map_time(self, args: List[Any]) -> Dict[str, Any]:
        """TIME(datetime) -> extract time part"""
        if not args:
            return {"$dateToString": {"date": "$$NOW", "format": "%H:%M:%S"}}
        
        date_expr = self._convert_date_arg(args[0])
        return {"$dateToString": {"date": date_expr, "format": "%H:%M:%S"}}
    
    # Date arithmetic implementations
    def _map_date_add(self, args: List[Any]) -> Dict[str, Any]:
        """DATE_ADD(date, INTERVAL expr unit) -> add interval to date"""
        if len(args) < 3:
            return {"$literal": "DATE_ADD requires date, interval value, and unit"}
        
        date_expr = self._convert_date_arg(args[0])
        interval_value = int(args[1]) if isinstance(args[1], (int, str)) else args[1]
        unit = str(args[2]).upper().strip("'\"")
        
        return self._add_date_interval(date_expr, interval_value, unit)
    
    def _map_date_sub(self, args: List[Any]) -> Dict[str, Any]:
        """DATE_SUB(date, INTERVAL expr unit) -> subtract interval from date"""
        if len(args) < 3:
            return {"$literal": "DATE_SUB requires date, interval value, and unit"}
        
        date_expr = self._convert_date_arg(args[0])
        interval_value = int(args[1]) if isinstance(args[1], (int, str)) else args[1]
        unit = str(args[2]).upper().strip("'\"")
        
        # Subtract by making the interval negative
        return self._add_date_interval(date_expr, -interval_value, unit)
    
    def _map_adddate(self, args: List[Any]) -> Dict[str, Any]:
        """ADDDATE(date, days) -> add days to date"""
        if len(args) < 2:
            return {"$literal": "ADDDATE requires date and days"}
        
        date_expr = self._convert_date_arg(args[0])
        days = int(args[1]) if isinstance(args[1], (int, str)) else args[1]
        
        return self._add_date_interval(date_expr, days, "DAY")
    
    def _map_subdate(self, args: List[Any]) -> Dict[str, Any]:
        """SUBDATE(date, days) -> subtract days from date"""
        if len(args) < 2:
            return {"$literal": "SUBDATE requires date and days"}
        
        date_expr = self._convert_date_arg(args[0])
        days = int(args[1]) if isinstance(args[1], (int, str)) else args[1]
        
        return self._add_date_interval(date_expr, -days, "DAY")
    
    def _map_datediff(self, args: List[Any]) -> Dict[str, Any]:
        """DATEDIFF(date1, date2) -> difference in days"""
        if len(args) < 2:
            return {"$literal": "DATEDIFF requires two dates"}
        
        date1_expr = self._convert_date_arg(args[0])
        date2_expr = self._convert_date_arg(args[1])
        
        # Calculate difference in milliseconds and convert to days
        return {
            "$toInt": {
                "$divide": [
                    {"$subtract": [date1_expr, date2_expr]},
                    86400000  # milliseconds in a day
                ]
            }
        }
    
    def _map_timediff(self, args: List[Any]) -> Dict[str, Any]:
        """TIMEDIFF(time1, time2) -> difference in time"""
        if len(args) < 2:
            return {"$literal": "TIMEDIFF requires two time expressions"}
        
        time1_expr = self._convert_date_arg(args[0])
        time2_expr = self._convert_date_arg(args[1])
        
        # Calculate difference in milliseconds and format as time
        diff_ms = {"$subtract": [time1_expr, time2_expr]}
        
        # Convert to time format (HH:MM:SS)
        return {
            "$dateToString": {
                "date": {"$add": [{"$literal": {"$date": "1970-01-01T00:00:00Z"}}, diff_ms]},
                "format": "%H:%M:%S"
            }
        }
    
    def _map_addtime(self, args: List[Any]) -> Dict[str, Any]:
        """ADDTIME(datetime, time) -> add time to datetime expression"""
        if len(args) < 2:
            return {"$literal": "ADDTIME requires datetime and time"}
        
        datetime_expr = self._convert_date_arg(args[0])
        time_str = str(args[1]).strip("'\"")
        
        # Use custom function for client-side evaluation
        return {"$addTime": {"datetime": datetime_expr, "time": time_str}}
    
    def _map_extract(self, args: List[Any]) -> Dict[str, Any]:
        """EXTRACT(unit FROM date) -> extract part of date/time"""
        if len(args) < 2:
            return {"$literal": "EXTRACT requires unit and date"}
        
        unit = str(args[0]).upper().strip("'\"")
        date_expr = self._convert_date_arg(args[1])
        
        # Map extract units to MongoDB date operators
        unit_map = {
            'YEAR': '$year',
            'MONTH': '$month',
            'DAY': '$dayOfMonth',
            'HOUR': '$hour',
            'MINUTE': '$minute',
            'SECOND': '$second',
            'MICROSECOND': {'$multiply': [{'$millisecond': date_expr}, 1000]},
            'WEEK': '$week',
            'QUARTER': {'$toInt': {'$ceil': {'$divide': [{'$month': date_expr}, 3]}}}
        }
        
        if unit in unit_map:
            if isinstance(unit_map[unit], str):
                return {unit_map[unit]: date_expr}
            else:
                return unit_map[unit]
        
        return {"$literal": f"Unsupported EXTRACT unit: {unit}"}
    
    def _map_timestampdiff(self, args: List[Any]) -> Dict[str, Any]:
        """TIMESTAMPDIFF(unit, date1, date2) -> difference in specified unit"""
        if len(args) < 3:
            return {"$literal": "TIMESTAMPDIFF requires unit, date1, and date2"}
        
        unit = str(args[0]).upper().strip("'\"")
        date1_expr = self._convert_date_arg(args[1])
        date2_expr = self._convert_date_arg(args[2])
        
        # Calculate difference in milliseconds first
        diff_ms = {"$subtract": [date2_expr, date1_expr]}
        
        # Convert to requested unit
        unit_map = {
            'MICROSECOND': {"$multiply": [diff_ms, 1000]},
            'SECOND': {"$divide": [diff_ms, 1000]},
            'MINUTE': {"$divide": [diff_ms, 60000]},
            'HOUR': {"$divide": [diff_ms, 3600000]},
            'DAY': {"$divide": [diff_ms, 86400000]},
            'WEEK': {"$divide": [diff_ms, 604800000]},
            'MONTH': {
                "$dateDiff": {
                    "startDate": date1_expr,
                    "endDate": date2_expr,
                    "unit": "month"
                }
            },
            'YEAR': {
                "$dateDiff": {
                    "startDate": date1_expr,
                    "endDate": date2_expr,
                    "unit": "year"
                }
            }
        }
        
        if unit in unit_map:
            return {"$toInt": unit_map[unit]}
        else:
            return {"$literal": f"Unsupported unit: {unit}"}
    
    def _map_timestampadd(self, args: List[Any]) -> Dict[str, Any]:
        """TIMESTAMPADD(unit, interval, date) -> add interval to date"""
        if len(args) < 3:
            return {"$literal": "TIMESTAMPADD requires unit, interval, and date"}
        
        unit = str(args[0]).upper().strip("'\"")
        interval = int(str(args[1]).strip("'\""))
        date_expr = self._convert_date_arg(args[2])
        
        # Use custom function that will be handled by client-side evaluation
        return {"$timestampAdd": {"unit": unit, "interval": interval, "date": date_expr}}
    
    def _map_last_day(self, args: List[Any]) -> Dict[str, Any]:
        """LAST_DAY(date) -> last day of month"""
        if not args:
            date_expr = "$$NOW"
        else:
            date_expr = self._convert_date_arg(args[0])
        
        # Calculate last day of month and return as date string
        last_day_date = {
            "$dateSubtract": {
                "startDate": {
                    "$dateFromParts": {
                        "year": {"$year": date_expr},
                        "month": {"$add": [{"$month": date_expr}, 1]},
                        "day": 1
                    }
                },
                "unit": "day",
                "amount": 1
            }
        }
        
        return {"$dateToString": {"date": last_day_date, "format": "%Y-%m-%d"}}
    
    def _map_makedate(self, args: List[Any]) -> Dict[str, Any]:
        """MAKEDATE(year, dayofyear) -> create date"""
        if len(args) < 2:
            return {"$literal": "MAKEDATE requires year and day of year"}
        
        year = int(str(args[0]).strip("'\""))
        day_of_year = int(str(args[1]).strip("'\""))
        
        # Create date from year and day of year and return as date string
        # Start with Jan 1 of the year, then add (dayofyear - 1) days
        date_result = {
            "$dateAdd": {
                "startDate": {
                    "$dateFromParts": {
                        "year": year,
                        "month": 1,
                        "day": 1
                    }
                },
                "unit": "day",
                "amount": day_of_year - 1
            }
        }
        
        return {"$dateToString": {"date": date_result, "format": "%Y-%m-%d"}}
    
    def _map_maketime(self, args: List[Any]) -> Dict[str, Any]:
        """MAKETIME(hour, minute, second) -> create time"""
        if len(args) < 3:
            return {"$literal": "MAKETIME requires hour, minute, and second"}
        
        hour = int(str(args[0]).strip("'\""))
        minute = int(str(args[1]).strip("'\""))
        second = int(str(args[2]).strip("'\""))
        
        # Create a time value by formatting as HH:MM:SS
        return {
            "$dateToString": {
                "date": {
                    "$dateFromParts": {
                        "year": 1970,
                        "month": 1,
                        "day": 1,
                        "hour": hour,
                        "minute": minute,
                        "second": second
                    }
                },
                "format": "%H:%M:%S"
            }
        }
    
    def _map_unix_timestamp(self, args: List[Any]) -> Dict[str, Any]:
        """UNIX_TIMESTAMP([date]) -> Unix timestamp"""
        if not args:
            return {"$divide": [{"$toLong": "$$NOW"}, 1000]}
        
        date_expr = self._convert_date_arg(args[0])
        return {"$divide": [{"$toLong": date_expr}, 1000]}
    
    def _map_from_unixtime(self, args: List[Any]) -> Dict[str, Any]:
        """FROM_UNIXTIME(unix_timestamp) -> datetime"""
        if not args:
            return {"$literal": "FROM_UNIXTIME requires timestamp argument"}
        
        timestamp = args[0]
        return {"$dateFromString": {"dateString": {"$toString": {"$multiply": [timestamp, 1000]}}}}
    
    def _map_from_days(self, args: List[Any]) -> Dict[str, Any]:
        """FROM_DAYS(day_number) -> date"""
        if not args:
            return {"$literal": "FROM_DAYS requires day number argument"}
        
        day_number = int(str(args[0]).strip("'\""))
        
        # MySQL day 0 = 0000-01-01, so we start from that base
        # MongoDB epoch is 1970-01-01, so we need to adjust
        base_date = {"$dateFromParts": {"year": 1, "month": 1, "day": 1}}
        
        return {
            "$dateAdd": {
                "startDate": base_date,
                "unit": "day", 
                "amount": day_number - 1
            }
        }
    
    def _map_to_days(self, args: List[Any]) -> Dict[str, Any]:
        """TO_DAYS(date) -> day number"""
        if not args:
            date_expr = "$$NOW"
        else:
            date_expr = self._convert_date_arg(args[0])
        
        # Use custom function to calculate TO_DAYS
        # This will be handled by the client-side evaluation
        return {"$toDays": date_expr}
    
    def _map_sec_to_time(self, args: List[Any]) -> Dict[str, Any]:
        """SEC_TO_TIME(seconds) -> time"""
        if not args:
            return {"$literal": "SEC_TO_TIME requires seconds argument"}
        
        seconds = int(str(args[0]).strip("'\""))
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        # Format as time string (no leading zero for hours, like MariaDB)
        return {"$literal": f"{hours}:{minutes:02d}:{secs:02d}"}
    
    def _map_time_to_sec(self, args: List[Any]) -> Dict[str, Any]:
        """TIME_TO_SEC(time) -> seconds"""
        if not args:
            return {"$literal": "TIME_TO_SEC requires time argument"}
        
        time_str = str(args[0]).strip("'\"")
        
        # Parse time string and convert to seconds
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) >= 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(float(parts[2]))
                total_seconds = hours * 3600 + minutes * 60 + seconds
                return {"$literal": total_seconds}
        
        return {"$literal": 0}
    
    def _map_subtime(self, args: List[Any]) -> Dict[str, Any]:
        """SUBTIME(datetime, time) -> subtract time from datetime"""
        if len(args) < 2:
            return {"$literal": "SUBTIME requires datetime and time arguments"}
        
        datetime_expr = self._convert_date_arg(args[0])
        time_str = str(args[1]).strip("'\"")
        
        # Use custom function for client-side evaluation
        return {"$subTime": {"datetime": datetime_expr, "time": time_str}}
    
    def _map_period_add(self, args: List[Any]) -> Dict[str, Any]:
        """PERIOD_ADD(period, months) -> add months to period"""
        if len(args) < 2:
            return {"$literal": "PERIOD_ADD requires period and months arguments"}
        
        period = int(str(args[0]).strip("'\""))
        months = int(str(args[1]).strip("'\""))
        
        # Period format is YYYYMM
        year = period // 100
        month = period % 100
        
        # Add months
        total_months = year * 12 + month + months
        new_year = total_months // 12
        new_month = total_months % 12
        if new_month == 0:
            new_month = 12
            new_year -= 1
        
        return {"$literal": new_year * 100 + new_month}
    
    def _map_period_diff(self, args: List[Any]) -> Dict[str, Any]:
        """PERIOD_DIFF(period1, period2) -> difference in months"""
        if len(args) < 2:
            return {"$literal": "PERIOD_DIFF requires two period arguments"}
        
        period1 = int(str(args[0]).strip("'\""))
        period2 = int(str(args[1]).strip("'\""))
        
        # Convert periods to months
        year1, month1 = period1 // 100, period1 % 100
        year2, month2 = period2 // 100, period2 % 100
        
        months1 = year1 * 12 + month1
        months2 = year2 * 12 + month2
        
        return {"$literal": months1 - months2}
    
    # Helper methods
    def _convert_date_arg(self, arg: Any) -> Any:
        """Convert a date argument to appropriate MongoDB expression."""
        if isinstance(arg, str):
            arg_clean = arg.strip("'\"")
            
            # Check if this is a function call (contains parentheses)
            if '(' in arg_clean and arg_clean.endswith(')'):
                # Extract function name
                func_name = arg_clean[:arg_clean.find('(')].strip().upper()
                
                # Handle common date/time functions
                if func_name in self.function_map:
                    # This is a date/time function - evaluate it
                    args_str = arg_clean[arg_clean.find('(')+1:-1].strip()
                    nested_args = []
                    if args_str:
                        # Simple argument parsing for nested calls
                        nested_args = [a.strip() for a in args_str.split(',')]
                    
                    # Get the result from the nested function
                    nested_result = self.function_map[func_name](nested_args)
                    
                    # For functions that return raw dates (like NOW, CURDATE, etc.), 
                    # extract the core date expression
                    if isinstance(nested_result, dict):
                        if '$dateToString' in nested_result and 'date' in nested_result['$dateToString']:
                            # Extract the raw date part for further processing
                            return nested_result['$dateToString']['date']
                        else:
                            # Return the full expression for non-formatting functions
                            return nested_result
                    else:
                        return nested_result
                else:
                    # Not a date function, treat as field reference
                    return f"${arg_clean}"
            
            # Check if it looks like a date string
            elif arg_clean.replace('-', '').replace(':', '').replace(' ', '').replace('T', '').replace('Z', '').isdigit():
                return {"$dateFromString": {"dateString": arg_clean}}
            else:
                # Treat as field reference
                return f"${arg_clean}" if not arg_clean.startswith('$') else arg_clean
        elif isinstance(arg, dict):
            # Already a MongoDB expression
            return arg
        else:
            # Convert to string and treat as field reference
            return f"${str(arg)}"
    
    def _add_date_interval(self, date_expr: Any, interval_value: int, unit: str) -> Dict[str, Any]:
        """Add an interval to a date expression using MongoDB's $dateAdd operator."""
        # MongoDB's $dateAdd operator (available in MongoDB 5.0+)
        # For older versions, we'll use manual calculation
        
        unit_map = {
            'YEAR': 'year',
            'MONTH': 'month', 
            'DAY': 'day',
            'HOUR': 'hour',
            'MINUTE': 'minute',
            'SECOND': 'second',
            'MICROSECOND': 'microsecond',
            'MILLISECOND': 'millisecond'
        }
        
        mongo_unit = unit_map.get(unit, 'day')
        
        # Use $dateAdd if available (MongoDB 5.0+), otherwise fallback to manual calculation
        try:
            return {
                "$dateAdd": {
                    "startDate": date_expr,
                    "unit": mongo_unit,
                    "amount": interval_value
                }
            }
        except:
            # Fallback for older MongoDB versions - convert to milliseconds and add
            if unit == 'DAY':
                ms_to_add = interval_value * 24 * 60 * 60 * 1000
            elif unit == 'HOUR':
                ms_to_add = interval_value * 60 * 60 * 1000
            elif unit == 'MINUTE':
                ms_to_add = interval_value * 60 * 1000
            elif unit == 'SECOND':
                ms_to_add = interval_value * 1000
            elif unit == 'MONTH':
                # Approximate: 30 days per month
                ms_to_add = interval_value * 30 * 24 * 60 * 60 * 1000
            elif unit == 'YEAR':
                # Approximate: 365 days per year
                ms_to_add = interval_value * 365 * 24 * 60 * 60 * 1000
            else:
                ms_to_add = interval_value * 24 * 60 * 60 * 1000  # Default to days
            
            return {"$add": [date_expr, ms_to_add]}
    
    def _convert_date_format(self, mysql_format: str) -> str:
        """Convert MySQL date format to MongoDB format (comprehensive mapping)."""
        # Comprehensive MySQL to MongoDB format conversion
        format_map = {
            # Year formats
            '%Y': '%Y',  # 4-digit year (2024)
            '%y': '%y',  # 2-digit year (24)
            
            # Month formats
            '%M': '%B',  # Full month name (January)
            '%b': '%b',  # Abbreviated month name (Jan)
            '%m': '%m',  # Month with leading zeros (01-12)
            '%c': '%m',  # Month without leading zeros (1-12) - approximate
            
            # Day formats
            '%d': '%d',  # Day with leading zeros (01-31)
            '%e': '%d',  # Day without leading zeros (1-31) - approximate
            '%D': '%d',  # Day with suffix (1st, 2nd, 3rd) - approximate
            '%j': '%j',  # Day of year (001-366)
            
            # Weekday formats
            '%W': '%A',  # Full weekday name (Monday)
            '%a': '%a',  # Abbreviated weekday name (Mon)
            '%w': '%w',  # Weekday as decimal (0=Sunday)
            
            # Hour formats
            '%H': '%H',  # Hour 24-hour format (00-23)
            '%h': '%I',  # Hour 12-hour format (01-12)
            '%I': '%I',  # Hour 12-hour format (01-12)
            '%k': '%H',  # Hour 24-hour format (0-23) - approximate
            '%l': '%I',  # Hour 12-hour format (1-12) - approximate
            
            # Minute/Second formats
            '%i': '%M',  # Minutes (00-59)
            '%s': '%S',  # Seconds (00-59)
            '%S': '%S',  # Seconds (00-59)
            '%f': '%L',  # Microseconds (000000-999999) - approximate with milliseconds
            
            # AM/PM formats
            '%p': '%p',  # AM or PM
            '%r': '%I:%M:%S %p',  # 12-hour time (hh:mm:ss AM/PM)
            '%T': '%H:%M:%S',     # 24-hour time (hh:mm:ss)
            
            # Week formats
            '%U': '%U',  # Week number (00-53) Sunday as first day
            '%u': '%U',  # Week number (00-53) Monday as first day - approximate
            '%V': '%V',  # Week number (01-53) - ISO week
            '%v': '%V',  # Week number (01-53) - approximate
            '%X': '%G',  # Year for the week (ISO) - approximate
            '%x': '%G',  # Year for the week - approximate
            
            # Common combined formats
            '%%': '%',   # Literal % character
        }
        
        result = mysql_format
        # Sort by length (longest first) to avoid partial replacements
        for mysql_fmt in sorted(format_map.keys(), key=len, reverse=True):
            mongo_fmt = format_map[mysql_fmt]
            result = result.replace(mysql_fmt, mongo_fmt)
        
        return result
    
    def _convert_timezone(self, tz_str: str) -> str:
        """Convert MySQL timezone format to MongoDB timezone format."""
        # Handle common timezone formats
        tz_map = {
            # UTC variants
            'UTC': 'UTC',
            '+00:00': 'UTC',
            'GMT': 'UTC',
            'Z': 'UTC',
            
            # Common named timezones
            'US/Eastern': 'America/New_York',
            'US/Central': 'America/Chicago',
            'US/Mountain': 'America/Denver',
            'US/Pacific': 'America/Los_Angeles',
            'Europe/London': 'Europe/London',
            'Europe/Paris': 'Europe/Paris',
            'Asia/Tokyo': 'Asia/Tokyo',
            'Australia/Sydney': 'Australia/Sydney',
            
            # Offset formats (keep as-is, MongoDB supports them)
            # '+05:30', '-08:00', etc.
        }
        
        # Return mapped timezone or original if not found
        return tz_map.get(tz_str, tz_str)