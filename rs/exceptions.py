class UpdateDocumentError(Exception):
    ...


class MissingPaperIdError(Exception):
    ...


class RequiredAbstractsAndReferencesError(Exception):
    ...


class RequiredPaperDOIorPaperURIError(Exception):
    ...


class UnableToAddConnectionError(Exception):
    ...


class SourceCreationInputError(Exception):
    ...


class SourceSearchInputError(Exception):
    ...


class ReferenceConnectionSearchInputError(Exception):
    ...


# class DocumentDoesNotExistError(Exception):
#     ...


# class FetchDocumentError(Exception):
#     ...


# class DBFetchDocumentError(Exception):
#     ...


# class DBFetchDocumentPackageError(Exception):
#     ...


# class DBCreateDocumentError(Exception):
#     ...


# class DBSaveDataError(Exception):
#     ...


# class DBConnectError(Exception):
#     ...


# class RemoteAndLocalFileError(Exception):
#     ...


# class ReceivedPackageRegistrationError(Exception):
#     ...


# class FilesStorageRegisterError(Exception):
#     ...


# class DBFetchMigratedDocError(Exception):
#     ...


# class MissingCisisPathEnvVarError(Exception):
#     ...


# class CisisPathNotFoundMigrationError(Exception):
#     ...


# class MissingI2IdCommandPathEnvVarError(Exception):
#     ...


# class IsisDBNotFoundError(Exception):
#     ...


# class IdFileNotFoundError(Exception):
#     ...


# class NotApplicableInfo(Exception):
#     ...


class InsuficientArgumentsToSearchDocumentError(Exception):
    ...


# class MissingRequiredV3Error(Exception):
#     ...


# class V3IsAlreadyRegisteredError(Exception):
#     ...


class DBSaveNotUniqueError(Exception):
    ...


# class DocumentIsNotNewError(Exception):
#     ...

class MissingRegisteredSources(Exception):
    ...


class BadPaperURIFormatError(Exception):
    ...


