# WHAT DOES THIS FILE DO: Custom exception classes so the pipeline can tell which stage failed instead of catching everything as a generic Exception.


# =========== VARIABLES : Shinrai's own exception hierarchy — every custom error in the app inherits from the base one ===========
class ShinraiException(Exception):
    ''' base exception for anything that goes wrong inside Shinrai '''
    pass


class CodeGenerationError(ShinraiException):
    ''' raised when GPT-4o fails to generate code from the prompt '''
    pass


class ReliabilityCheckError(ShinraiException):
    ''' raised when the reliability check layer itself blows up, not when a check just scores low '''
    pass


class SecurityCheckError(ShinraiException):
    ''' raised when the security check layer itself blows up, not when a check just scores low '''
    pass


class RepairError(ShinraiException):
    ''' raised when the GPT-4o repair call fails '''
    pass


class DatabaseError(ShinraiException):
    ''' raised when a database read or write fails '''
    pass
# =========== VARIABLES : Shinrai's own exception hierarchy — every custom error in the app inherits from the base one ===========
