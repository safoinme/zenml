---
description: How to develop a custom artifact store
---

ZenML comes equipped with [Artifact Store implementations](./artifact-stores.md#artifact-store-flavors)
that you can use to store artifacts on a local filesystem or in the managed AWS,
GCP or Azure cloud object storage services. However, if you need to use a
different type of object storage service as a backend for your ZenML Artifact
Store, you can extend ZenML to provide your own custom Artifact Store
implementation.

## Base Abstraction

The Artifact Store establishes one of the main components in every ZenML stack.
Now, let us take a deeper dive into the fundamentals behind its abstraction,
namely [the `BaseArtifactStore` class](https://apidocs.zenml.io/latest/core_code_docs/core-artifact_stores/#zenml.artifact_stores.base_artifact_store.BaseArtifactStore):

1. As ZenML only supports filesystem-based artifact stores, it features a 
configuration parameter called `path`, which will indicate the root path of 
the artifact store. When registering an artifact store, users will have to 
define this parameter.
2. Moreover, there is another variable in the config class called 
`SUPPORTED_SCHEMES`. This is a class variable that needs to be defined 
in every subclass of the base artifact store configuration. It indicates the 
supported filepath schemes for the corresponding implementation. For instance, 
for the Azure artifact store, this set will be defined as 
`{"abfs://", "az://"}`.
3. Lastly, the base class features a set of `abstractmethod`s: `open`,
`copyfile`,`exists`,`glob`,`isdir`,`listdir`,`makedirs`,`mkdir`,`remove`,
`rename`,`rmtree`,`stat`,`walk`. In the implementation of every 
`ArtifactStore` flavor, it is required to define these methods with respect 
to the flavor at hand.

Putting all these considerations together, we end up with the following 
implementation:

```python

from zenml.enums import StackComponentType
from zenml.stack import StackComponent, StackComponentConfig

PathType = Union[bytes, str]


class BaseArtifactStoreConfig(StackComponentConfig):
    """Config class for `BaseArtifactStore`."""

    path: str

    SUPPORTED_SCHEMES: ClassVar[Set[str]]


class BaseArtifactStore(StackComponent):
    """Base class for all ZenML artifact stores."""

    @abstractmethod
    def open(self, name: PathType, mode: str = "r") -> Any:
        """Open a file at the given path."""

    @abstractmethod
    def copyfile(
        self, src: PathType, dst: PathType, overwrite: bool = False
    ) -> None:
        """Copy a file from the source to the destination."""

    @abstractmethod
    def exists(self, path: PathType) -> bool:
        """Returns `True` if the given path exists."""

    @abstractmethod
    def glob(self, pattern: PathType) -> List[PathType]:
        """Return the paths that match a glob pattern."""

    @abstractmethod
    def isdir(self, path: PathType) -> bool:
        """Returns whether the given path points to a directory."""

    @abstractmethod
    def listdir(self, path: PathType) -> List[PathType]:
        """Returns a list of files under a given directory in the filesystem."""

    @abstractmethod
    def makedirs(self, path: PathType) -> None:
        """Make a directory at the given path, recursively creating parents."""

    @abstractmethod
    def mkdir(self, path: PathType) -> None:
        """Make a directory at the given path; parent directory must exist."""

    @abstractmethod
    def remove(self, path: PathType) -> None:
        """Remove the file at the given path. Dangerous operation."""

    @abstractmethod
    def rename(
        self, src: PathType, dst: PathType, overwrite: bool = False
    ) -> None:
        """Rename source file to destination file."""

    @abstractmethod
    def rmtree(self, path: PathType) -> None:
        """Deletes dir recursively. Dangerous operation."""

    @abstractmethod
    def stat(self, path: PathType) -> Any:
        """Return the stat descriptor for a given file path."""

    @abstractmethod
    def walk(
        self,
        top: PathType,
        topdown: bool = True,
        onerror: Optional[Callable[..., None]] = None,
    ) -> Iterable[Tuple[PathType, List[PathType], List[PathType]]]:
        """Return an iterator that walks the contents of the given directory."""

        
class BaseArtifactStoreFlavor(Flavor):
    """Base class for artifact store flavors."""

    @property
    @abstractmethod
    def name(self) -> Type["BaseArtifactStore"]:
        """Returns the name of the flavor."""
        
    @property
    def type(self) -> StackComponentType:
        """Returns the flavor type."""
        return StackComponentType.ARTIFACT_STORE

    @property
    def config_class(self) -> Type[StackComponentConfig]:
        """Config class."""
        return BaseArtifactStoreConfig

    @property
    @abstractmethod
    def implementation_class(self) -> Type["BaseArtifactStore"]:
        """Implementation class."""
```

{% hint style="info" %}
This is a slimmed-down version of the base implementation which aims to 
highlight the abstraction layer. In order to see the full implementation 
and get the complete docstrings, please check the [API docs](https://apidocs.zenml.io/latest/core_code_docs/core-artifact_stores/#zenml.artifact_stores.base_artifact_store.BaseArtifactStore).
{% endhint %}

#### The effect on the `zenml.io.fileio`

If you created an instance of an artifact store, added it to your stack and 
activated the stack, it will create a filesystem each time you run a ZenML 
pipeline and make it available to the `zenml.io.fileio` module. 

This means that when you utilize a method such as `fileio.open(...)` with a 
filepath which starts with one of the `SUPPORTED_SCHEMES` within 
your steps or materializers, it will be able to use the `open(...)` method 
that you defined within your artifact store.

## Build your own custom artifact store

If you want to implement your own custom Artifact Store, you can 
follow the following steps:

1. Create a class which inherits from [the `BaseArtifactStore` class](https://apidocs.zenml.io/latest/core_code_docs/core-artifact_stores/#zenml.artifact_stores.base_artifact_store.BaseArtifactStore)
and implement the abstract methods.
2. Create a class which inherits from [the `BaseArtifactStoreConfig` class]() 
and fill in the `SUPPORTED_SCHEMES` based on your file system.
3. Bring both of these classes together by inheriting from [the
`BaseArtifactStoreFlavor` class]().

Once you are done with the implementation, you can register it through the CLI 
as:

```shell
zenml artifact-store flavor register <THE-SOURCE-PATH-OF-YOUR-ARTIFACT-STORE-FLAVOR>
```

{% hint style="warning" %}
It is important to draw attention to when and how these base abstractions are 
coming into play in a ZenML workflow.

- The **CustomArtifactStoreFlavor** class is imported and utilized upon the 
creation of the custom flavor through the CLI.
- The **CustomArtifactStoreConfig** class is imported when someone tries to 
register/update a stack component with this custom flavor. Especially, 
during the registration process of the stack component, the config will be used 
to validate the values given by the user. As `Config` object are inherently 
`pydantic` objects, you can also add your own custom validators here.
- The **CustomArtifactStore** only comes into play when the component is 
ultimately in use. 

The design behind this interaction lets us separate the configuration of the 
flavor from its implementation. This way we can register flavors and components 
even when the major dependencies behind their implementation are not installed
in our local setting (assuming the `CustomArtifactStoreFlavor` and the 
`CustomArtifactStoreConfig` are implemented in a different module/path than 
the actual `CustomArtifactStore`).
{% endhint %}