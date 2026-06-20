# # """
# # Comprehensive mock triton module for Mac M3 Max compatibility
# # Based on actual triton source structure with complete math module
# # """

# # import sys
# # import os
# # from types import ModuleType
# # from importlib.machinery import ModuleSpec
# # import warnings

# # def create_mock_module(name, parent_name=None):
# #     """Create a properly structured mock module"""
# #     module = ModuleType(name)
    
# #     # Create proper module spec
# #     spec = ModuleSpec(name, None)
# #     spec.origin = "mock"
# #     spec.submodule_search_locations = [] if parent_name else [f"mock_{name}"]
# #     module.__spec__ = spec
# #     module.__name__ = name
# #     module.__file__ = "<mock>"
# #     module.__package__ = parent_name if parent_name else name.split('.')[0]
# #     module.__path__ = [f"mock_{name}"] if not parent_name else []
    
# #     return module

# # # Create a more sophisticated mock class that handles .value attribute access
# # class MockTritonType:
# #     """Mock class that can be used as both a callable and a type"""
# #     def __init__(self, name="MockTritonType", value=None):
# #         self.name = name
# #         self._value = value
    
# #     @property
# #     def value(self):
# #         """Handle .value attribute access"""
# #         return self._value if self._value is not None else self
    
# #     def __call__(self, *args, **kwargs):
# #         warnings.warn(f"Using mock {self.name} for Mac compatibility", UserWarning, stacklevel=2)
# #         return self
    
# #     def __getattr__(self, name):
# #         return MockTritonType(f"{self.name}.{name}")
    
# #     def __getitem__(self, item):
# #         return MockTritonType(f"{self.name}[{item}]")
    
# #     def __int__(self):
# #         """Handle int conversion"""
# #         return 0
    
# #     def __float__(self):
# #         """Handle float conversion"""
# #         return 0.0
    
# #     def __bool__(self):
# #         """Handle bool conversion"""
# #         return True
    
# #     def __str__(self):
# #         return f"MockTritonType({self.name})"
    
# #     def __repr__(self):
# #         return f"<MockTritonType: {self.name}>"

# # # Create mock enum-like classes for data types
# # class MockDataType:
# #     """Mock data type that behaves like an enum"""
# #     def __init__(self, name, size_bytes=4):
# #         self.name = name
# #         self.size_bytes = size_bytes
# #         self.value = self
    
# #     def __str__(self):
# #         return self.name
    
# #     def __repr__(self):
# #         return f"MockDataType({self.name})"
    
# #     def __call__(self, *args, **kwargs):
# #         return self
    
# #     def __getattr__(self, name):
# #         return MockTritonType(f"{self.name}.{name}")

# # # Mock triton functions
# # def mock_triton_jit(*args, **kwargs):
# #     """Mock triton.jit decorator"""
# #     def decorator(func):
# #         return func
# #     return decorator

# # def mock_triton_cdiv(a, b):
# #     """Mock ceiling division"""
# #     return (a + b - 1) // b

# # def mock_constexpr(value):
# #     """Mock constexpr function"""
# #     return value

# # def mock_autotune(*args, **kwargs):
# #     """Mock autotune decorator"""
# #     def decorator(func):
# #         return func
# #     return decorator

# # def mock_next_power_of_2(x):
# #     """Mock next_power_of_2 function"""
# #     if x <= 0:
# #         return 1
# #     return 1 << (x - 1).bit_length()

# # def mock_config(*args, **kwargs):
# #     """Mock Config class"""
# #     class MockConfig:
# #         def __init__(self, **kwargs):
# #             for k, v in kwargs.items():
# #                 setattr(self, k, v)
# #     return MockConfig(**kwargs)

# # def mock_heuristics(*args, **kwargs):
# #     """Mock heuristics function"""
# #     return MockTritonType("heuristics")

# # # Create main triton module
# # triton_module = create_mock_module('triton')
# # triton_module.jit = mock_triton_jit
# # triton_module.cdiv = mock_triton_cdiv
# # triton_module.next_power_of_2 = mock_next_power_of_2
# # triton_module.Config = mock_config
# # triton_module.autotune = mock_autotune
# # triton_module.heuristics = mock_heuristics
# # triton_module.__version__ = "2.1.0"

# # # Create triton.language as a package (not just a module)
# # triton_language = create_mock_module('triton.language', 'triton')

# # # Add all the attributes from the actual triton.language.__init__.py
# # triton_language.program_id = MockTritonType("program_id")
# # triton_language.num_programs = MockTritonType("num_programs")
# # triton_language.arange = MockTritonType("arange")
# # triton_language.load = MockTritonType("load")
# # triton_language.store = MockTritonType("store")
# # triton_language.atomic_add = MockTritonType("atomic_add")
# # triton_language.atomic_cas = MockTritonType("atomic_cas")
# # triton_language.atomic_xchg = MockTritonType("atomic_xchg")
# # triton_language.atomic_max = MockTritonType("atomic_max")
# # triton_language.atomic_min = MockTritonType("atomic_min")
# # triton_language.atomic_and = MockTritonType("atomic_and")
# # triton_language.atomic_or = MockTritonType("atomic_or")
# # triton_language.atomic_xor = MockTritonType("atomic_xor")
# # triton_language.dot = MockTritonType("dot")
# # triton_language.dot_scaled = MockTritonType("dot_scaled")
# # triton_language.trans = MockTritonType("trans")
# # triton_language.broadcast_to = MockTritonType("broadcast_to")
# # triton_language.sum = MockTritonType("sum")
# # triton_language.max = MockTritonType("max")
# # triton_language.min = MockTritonType("min")
# # triton_language.maximum = MockTritonType("maximum")
# # triton_language.minimum = MockTritonType("minimum")
# # triton_language.where = MockTritonType("where")
# # triton_language.exp = MockTritonType("exp")
# # triton_language.exp2 = MockTritonType("exp2")
# # triton_language.log = MockTritonType("log")
# # triton_language.log2 = MockTritonType("log2")
# # triton_language.log10 = MockTritonType("log10")
# # triton_language.sqrt = MockTritonType("sqrt")
# # triton_language.rsqrt = MockTritonType("rsqrt")
# # triton_language.sin = MockTritonType("sin")
# # triton_language.cos = MockTritonType("cos")
# # triton_language.tan = MockTritonType("tan")
# # triton_language.asin = MockTritonType("asin")
# # triton_language.acos = MockTritonType("acos")
# # triton_language.atan = MockTritonType("atan")
# # triton_language.atan2 = MockTritonType("atan2")
# # triton_language.sinh = MockTritonType("sinh")
# # triton_language.cosh = MockTritonType("cosh")
# # triton_language.tanh = MockTritonType("tanh")
# # triton_language.asinh = MockTritonType("asinh")
# # triton_language.acosh = MockTritonType("acosh")
# # triton_language.atanh = MockTritonType("atanh")
# # triton_language.floor = MockTritonType("floor")
# # triton_language.ceil = MockTritonType("ceil")
# # triton_language.round = MockTritonType("round")
# # triton_language.trunc = MockTritonType("trunc")
# # triton_language.fmod = MockTritonType("fmod")
# # triton_language.remainder = MockTritonType("remainder")
# # triton_language.abs = MockTritonType("abs")
# # triton_language.pow = MockTritonType("pow")
# # triton_language.clamp = MockTritonType("clamp")
# # triton_language.constexpr = mock_constexpr
# # triton_language.constexpr_function = MockTritonType("constexpr_function")
# # triton_language.const = MockTritonType("const")
# # triton_language.multiple_of = MockTritonType("multiple_of")
# # triton_language.max_constancy = MockTritonType("max_constancy")
# # triton_language.max_contiguous = MockTritonType("max_contiguous")
# # triton_language.static_print = MockTritonType("static_print")
# # triton_language.static_assert = MockTritonType("static_assert")
# # triton_language.static_range = MockTritonType("static_range")
# # triton_language.device_print = MockTritonType("device_print")
# # triton_language.device_assert = MockTritonType("device_assert")
# # triton_language.debug_barrier = MockTritonType("debug_barrier")

# # # Data types - use MockDataType for proper enum-like behavior
# # triton_language.int1 = MockDataType("int1", 1)
# # triton_language.int8 = MockDataType("int8", 1)
# # triton_language.int16 = MockDataType("int16", 2)
# # triton_language.int32 = MockDataType("int32", 4)
# # triton_language.int64 = MockDataType("int64", 8)
# # triton_language.uint8 = MockDataType("uint8", 1)
# # triton_language.uint16 = MockDataType("uint16", 2)
# # triton_language.uint32 = MockDataType("uint32", 4)
# # triton_language.uint64 = MockDataType("uint64", 8)
# # triton_language.float16 = MockDataType("float16", 2)
# # triton_language.float32 = MockDataType("float32", 4)
# # triton_language.float64 = MockDataType("float64", 8)
# # triton_language.bfloat16 = MockDataType("bfloat16", 2)
# # triton_language.float8e4b15 = MockDataType("float8e4b15", 1)
# # triton_language.float8e4nv = MockDataType("float8e4nv", 1)
# # triton_language.float8e4b8 = MockDataType("float8e4b8", 1)
# # triton_language.float8e5 = MockDataType("float8e5", 1)
# # triton_language.float8e5b16 = MockDataType("float8e5b16", 1)
# # triton_language.float8e4m3fn = MockDataType("float8e4m3fn", 1)
# # triton_language.float8e5m2 = MockDataType("float8e5m2", 1)

# # # Additional functions from triton.language.__init__.py
# # triton_language.zeros = MockTritonType("zeros")
# # triton_language.zeros_like = MockTritonType("zeros_like")
# # triton_language.full = MockTritonType("full")
# # triton_language.full_like = MockTritonType("full_like")
# # triton_language.reshape = MockTritonType("reshape")
# # triton_language.view = MockTritonType("view")
# # triton_language.permute = MockTritonType("permute")
# # triton_language.transpose = MockTritonType("transpose")
# # triton_language.expand_dims = MockTritonType("expand_dims")
# # triton_language.squeeze = MockTritonType("squeeze")
# # triton_language.ravel = MockTritonType("ravel")
# # triton_language.range = MockTritonType("range")
# # triton_language.reduce = MockTritonType("reduce")
# # triton_language.slice = MockTritonType("slice")
# # triton_language.split = MockTritonType("split")
# # triton_language.join = MockTritonType("join")
# # triton_language.cat = MockTritonType("cat")
# # triton_language.gather = MockTritonType("gather")
# # triton_language.scatter = MockTritonType("scatter")
# # triton_language.histogram = MockTritonType("histogram")
# # triton_language.make_block_ptr = MockTritonType("make_block_ptr")
# # triton_language.advance = MockTritonType("advance")
# # triton_language.inline_asm_elementwise = MockTritonType("inline_asm_elementwise")
# # triton_language.dtype = MockTritonType("dtype")
# # triton_language.tensor = MockTritonType("tensor")
# # triton_language.tuple = MockTritonType("tuple")
# # triton_language.tuple_type = MockTritonType("tuple_type")
# # triton_language.pointer_type = MockTritonType("pointer_type")
# # triton_language.pi32_t = MockTritonType("pi32_t")
# # triton_language.semantic = MockTritonType("semantic")

# # # Create comprehensive triton.language.math submodule
# # triton_language_math = create_mock_module('triton.language.math', 'triton.language')

# # # All mathematical functions from triton.language.math
# # triton_language_math.abs = MockTritonType("math.abs")
# # triton_language_math.acos = MockTritonType("math.acos")
# # triton_language_math.acosh = MockTritonType("math.acosh")
# # triton_language_math.asin = MockTritonType("math.asin")
# # triton_language_math.asinh = MockTritonType("math.asinh")
# # triton_language_math.atan = MockTritonType("math.atan")
# # triton_language_math.atan2 = MockTritonType("math.atan2")
# # triton_language_math.atanh = MockTritonType("math.atanh")
# # triton_language_math.ceil = MockTritonType("math.ceil")
# # triton_language_math.clamp = MockTritonType("math.clamp")
# # triton_language_math.cos = MockTritonType("math.cos")
# # triton_language_math.cosh = MockTritonType("math.cosh")
# # triton_language_math.erf = MockTritonType("math.erf")
# # triton_language_math.erfc = MockTritonType("math.erfc")
# # triton_language_math.exp = MockTritonType("math.exp")
# # triton_language_math.exp2 = MockTritonType("math.exp2")
# # triton_language_math.expm1 = MockTritonType("math.expm1")
# # triton_language_math.fabs = MockTritonType("math.fabs")
# # triton_language_math.floor = MockTritonType("math.floor")
# # triton_language_math.fmod = MockTritonType("math.fmod")
# # triton_language_math.frexp = MockTritonType("math.frexp")
# # triton_language_math.gamma = MockTritonType("math.gamma")
# # triton_language_math.isfinite = MockTritonType("math.isfinite")
# # triton_language_math.isinf = MockTritonType("math.isinf")
# # triton_language_math.isnan = MockTritonType("math.isnan")
# # triton_language_math.j0 = MockTritonType("math.j0")
# # triton_language_math.j1 = MockTritonType("math.j1")
# # triton_language_math.ldexp = MockTritonType("math.ldexp")
# # triton_language_math.lgamma = MockTritonType("math.lgamma")
# # triton_language_math.log = MockTritonType("math.log")
# # triton_language_math.log10 = MockTritonType("math.log10")
# # triton_language_math.log1p = MockTritonType("math.log1p")
# # triton_language_math.log2 = MockTritonType("math.log2")
# # triton_language_math.logb = MockTritonType("math.logb")
# # triton_language_math.modf = MockTritonType("math.modf")
# # triton_language_math.nearbyint = MockTritonType("math.nearbyint")
# # triton_language_math.nextafter = MockTritonType("math.nextafter")
# # triton_language_math.pow = MockTritonType("math.pow")
# # triton_language_math.remainder = MockTritonType("math.remainder")
# # triton_language_math.rint = MockTritonType("math.rint")
# # triton_language_math.round = MockTritonType("math.round")
# # triton_language_math.rsqrt = MockTritonType("math.rsqrt")
# # triton_language_math.scalb = MockTritonType("math.scalb")
# # triton_language_math.sin = MockTritonType("math.sin")
# # triton_language_math.sinh = MockTritonType("math.sinh")
# # triton_language_math.sqrt = MockTritonType("math.sqrt")
# # triton_language_math.tan = MockTritonType("math.tan")
# # triton_language_math.tanh = MockTritonType("math.tanh")
# # triton_language_math.tgamma = MockTritonType("math.tgamma")
# # triton_language_math.trunc = MockTritonType("math.trunc")
# # triton_language_math.y0 = MockTritonType("math.y0")
# # triton_language_math.y1 = MockTritonType("math.y1")

# # # Add math submodule to triton.language
# # triton_language.math = triton_language_math

# # # Create triton.ops module
# # triton_ops = create_mock_module('triton.ops', 'triton')
# # triton_ops.matmul = MockTritonType("ops.matmul")
# # triton_ops.addmm = MockTritonType("ops.addmm")
# # triton_ops.conv = MockTritonType("ops.conv")
# # triton_ops.flash_attention = MockTritonType("ops.flash_attention")

# # # Create triton.runtime module and submodules
# # triton_runtime = create_mock_module('triton.runtime', 'triton')
# # triton_runtime.driver = create_mock_module('triton.runtime.driver', 'triton.runtime')
# # triton_runtime.driver.active = create_mock_module('triton.runtime.driver.active', 'triton.runtime.driver')

# # # Create triton.runtime.autotuner module
# # triton_runtime_autotuner = create_mock_module('triton.runtime.autotuner', 'triton.runtime')
# # triton_runtime_autotuner.Autotuner = MockTritonType("autotuner.Autotuner")
# # triton_runtime_autotuner.Config = MockTritonType("autotuner.Config")
# # triton_runtime_autotuner.Heuristics = MockTritonType("autotuner.Heuristics")
# # triton_runtime_autotuner.autotune = mock_autotune
# # triton_runtime_autotuner.heuristics = mock_heuristics

# # # Create triton.runtime.jit module
# # triton_runtime_jit = create_mock_module('triton.runtime.jit', 'triton.runtime')
# # triton_runtime_jit.JITFunction = MockTritonType("jit.JITFunction")
# # triton_runtime_jit.KernelInterface = MockTritonType("jit.KernelInterface")
# # triton_runtime_jit.MockTensor = MockTritonType("jit.MockTensor")
# # triton_runtime_jit.TensorWrapper = MockTritonType("jit.TensorWrapper")
# # triton_runtime_jit.reinterpret = MockTritonType("jit.reinterpret")

# # # Create triton.runtime.cache module
# # triton_runtime_cache = create_mock_module('triton.runtime.cache', 'triton.runtime')
# # triton_runtime_cache.get_cache_manager = MockTritonType("cache.get_cache_manager")
# # triton_runtime_cache.get_dump_manager = MockTritonType("cache.get_dump_manager")

# # # Create triton.runtime.errors module
# # triton_runtime_errors = create_mock_module('triton.runtime.errors', 'triton.runtime')
# # triton_runtime_errors.OutOfResources = MockTritonType("errors.OutOfResources")
# # triton_runtime_errors.InterpreterError = MockTritonType("errors.InterpreterError")

# # # Create triton.testing module
# # triton_testing = create_mock_module('triton.testing', 'triton')
# # triton_testing.perf_report = MockTritonType("testing.perf_report")
# # triton_testing.do_bench = MockTritonType("testing.do_bench")
# # triton_testing.assert_close = MockTritonType("testing.assert_close")

# # # Create triton.compiler module
# # triton_compiler = create_mock_module('triton.compiler', 'triton')
# # triton_compiler.compile = MockTritonType("compiler.compile")
# # triton_compiler.CompiledKernel = MockTritonType("compiler.CompiledKernel")

# # # Create triton.heuristics module
# # triton_heuristics = create_mock_module('triton.heuristics', 'triton')
# # triton_heuristics.matmul = MockTritonType("heuristics.matmul")
# # triton_heuristics.addmm = MockTritonType("heuristics.addmm")

# # # Create triton.profiler module
# # triton_profiler = create_mock_module('triton.profiler', 'triton')
# # triton_profiler.profile = MockTritonType("profiler.profile")
# # triton_profiler.Profiler = MockTritonType("profiler.Profiler")

# # # Install all triton mock modules
# # sys.modules['triton'] = triton_module
# # sys.modules['triton.language'] = triton_language
# # sys.modules['triton.language.math'] = triton_language_math
# # sys.modules['triton.ops'] = triton_ops
# # sys.modules['triton.runtime'] = triton_runtime
# # sys.modules['triton.runtime.driver'] = triton_runtime.driver
# # sys.modules['triton.runtime.driver.active'] = triton_runtime.driver.active
# # sys.modules['triton.runtime.autotuner'] = triton_runtime_autotuner
# # sys.modules['triton.runtime.jit'] = triton_runtime_jit
# # sys.modules['triton.runtime.cache'] = triton_runtime_cache
# # sys.modules['triton.runtime.errors'] = triton_runtime_errors
# # sys.modules['triton.testing'] = triton_testing
# # sys.modules['triton.compiler'] = triton_compiler
# # sys.modules['triton.heuristics'] = triton_heuristics
# # sys.modules['triton.profiler'] = triton_profiler

# # # Make sure triton.language is recognized as a package
# # triton_language.__path__ = ['mock_triton_language']

# # print("[Mock] Enhanced triton modules installed for Mac compatibility")
# # print("[Mock] - triton.language (package with complete math module)")
# # print("[Mock] - triton.language.math (with tanh, tan, and all math functions)")
# # print("[Mock] - triton.runtime.autotuner")
# # print("[Mock] - triton.runtime.jit")
# # print("[Mock] - triton.runtime.cache")
# # print("[Mock] - triton.runtime.errors")
# # print("[Mock] - triton.testing")
# # print("[Mock] - triton.compiler")
# # print("[Mock] - triton.profiler")
# # print("[Mock] - Data types with proper .value attribute support")
# # print("[Mock] - All other triton submodules")


























# """
# Enhanced mock triton module with robust .value attribute handling
# """

# import sys
# import os
# from types import ModuleType
# from importlib.machinery import ModuleSpec
# import warnings

# def create_mock_module(name, parent_name=None):
#     """Create a properly structured mock module"""
#     module = ModuleType(name)
    
#     # Create proper module spec
#     spec = ModuleSpec(name, None)
#     spec.origin = "mock"
#     spec.submodule_search_locations = [] if parent_name else [f"mock_{name}"]
#     module.__spec__ = spec
#     module.__name__ = name
#     module.__file__ = "<mock>"
#     module.__package__ = parent_name if parent_name else name.split('.')[0]
#     module.__path__ = [f"mock_{name}"] if not parent_name else []
    
#     return module

# # Enhanced mock class with better .value handling
# class MockTritonType:
#     """Mock class that can be used as both a callable and a type"""
#     def __init__(self, name="MockTritonType", value=None):
#         self.name = name
#         self._value = value
#         # Make sure we have a proper value attribute
#         if hasattr(self, '__dict__'):
#             self.__dict__['value'] = value if value is not None else self
    
#     def __getattr__(self, name):
#         if name == 'value':
#             return self._value if self._value is not None else self
#         return MockTritonType(f"{self.name}.{name}")
    
#     def __setattr__(self, name, value):
#         if name == 'value':
#             self._value = value
#         super().__setattr__(name, value)
    
#     @property
#     def value(self):
#         """Handle .value attribute access"""
#         return self._value if self._value is not None else self
    
#     def __call__(self, *args, **kwargs):
#         warnings.warn(f"Using mock {self.name} for Mac compatibility", UserWarning, stacklevel=2)
#         return self
    
#     def __getitem__(self, item):
#         return MockTritonType(f"{self.name}[{item}]")
    
#     def __int__(self):
#         return 0
    
#     def __float__(self):
#         return 0.0
    
#     def __bool__(self):
#         return True
    
#     def __str__(self):
#         return f"MockTritonType({self.name})"
    
#     def __repr__(self):
#         return f"<MockTritonType: {self.name}>"

# # Enhanced mock data type with explicit value handling
# class MockDataType:
#     """Mock data type that behaves like an enum with explicit value handling"""
#     def __init__(self, name, size_bytes=4):
#         self.name = name
#         self.size_bytes = size_bytes
#         # Explicitly set the value attribute
#         self._value = self
        
#     @property
#     def value(self):
#         """Always return self for .value access"""
#         return self._value
    
#     @value.setter
#     def value(self, val):
#         self._value = val
    
#     def __getattr__(self, name):
#         if name == 'value':
#             return self._value
#         return MockTritonType(f"{self.name}.{name}")
    
#     def __str__(self):
#         return self.name
    
#     def __repr__(self):
#         return f"MockDataType({self.name})"
    
#     def __call__(self, *args, **kwargs):
#         return self
    
#     def __int__(self):
#         return self.size_bytes
    
#     def __float__(self):
#         return float(self.size_bytes)

# # Patch the builtin int type to handle .value gracefully
# _original_int_getattribute = int.__getattribute__

# def _patched_int_getattribute(self, name):
#     if name == 'value':
#         # Return the int itself when .value is accessed
#         return self
#     return _original_int_getattribute(self, name)

# # Apply the patch
# int.__getattribute__ = _patched_int_getattribute

# print("[Enhanced Mock] Applied int.value patch for triton compatibility")

# # Create triton mock with enhanced error handling
# def mock_triton_jit(*args, **kwargs):
#     def decorator(func):
#         return func
#     return decorator

# def mock_triton_cdiv(a, b):
#     return (a + b - 1) // b

# def mock_constexpr(value):
#     """Enhanced constexpr that handles .value access"""
#     class ConstExprValue:
#         def __init__(self, val):
#             self._val = val
#             self.value = val
        
#         def __getattr__(self, name):
#             if name == 'value':
#                 return self._val
#             return getattr(self._val, name, None)
        
#         def __call__(self, *args, **kwargs):
#             return self._val
        
#         def __str__(self):
#             return str(self._val)
        
#         def __repr__(self):
#             return f"ConstExpr({self._val})"
        
#         def __int__(self):
#             return int(self._val)
        
#         def __float__(self):
#             return float(self._val)
    
#     return ConstExprValue(value)

# def mock_autotune(*args, **kwargs):
#     def decorator(func):
#         return func
#     return decorator

# def mock_next_power_of_2(x):
#     if x <= 0:
#         return 1
#     return 1 << (x - 1).bit_length()

# def mock_config(*args, **kwargs):
#     class MockConfig:
#         def __init__(self, **kwargs):
#             for k, v in kwargs.items():
#                 setattr(self, k, v)
#     return MockConfig(**kwargs)

# def mock_heuristics(*args, **kwargs):
#     return MockTritonType("heuristics")

# # Create main triton module with enhanced mocks
# triton_module = create_mock_module('triton')
# triton_module.jit = mock_triton_jit
# triton_module.cdiv = mock_triton_cdiv
# triton_module.next_power_of_2 = mock_next_power_of_2
# triton_module.Config = mock_config
# triton_module.autotune = mock_autotune
# triton_module.heuristics = mock_heuristics
# triton_module.__version__ = "2.1.0"

# # Create triton.language with enhanced types
# triton_language = create_mock_module('triton.language', 'triton')

# # Add enhanced function mocks
# triton_language.program_id = MockTritonType("program_id")
# triton_language.num_programs = MockTritonType("num_programs")
# triton_language.arange = MockTritonType("arange")
# triton_language.load = MockTritonType("load")
# triton_language.store = MockTritonType("store")
# triton_language.atomic_add = MockTritonType("atomic_add")
# triton_language.dot = MockTritonType("dot")
# triton_language.sum = MockTritonType("sum")
# triton_language.max = MockTritonType("max")
# triton_language.min = MockTritonType("min")
# triton_language.where = MockTritonType("where")
# triton_language.exp = MockTritonType("exp")
# triton_language.log = MockTritonType("log")
# triton_language.sqrt = MockTritonType("sqrt")
# triton_language.sin = MockTritonType("sin")
# triton_language.cos = MockTritonType("cos")
# triton_language.tan = MockTritonType("tan")
# triton_language.tanh = MockTritonType("tanh")
# triton_language.constexpr = mock_constexpr

# # Enhanced data types with explicit value handling
# triton_language.int8 = MockDataType("int8", 1)
# triton_language.int16 = MockDataType("int16", 2)
# triton_language.int32 = MockDataType("int32", 4)
# triton_language.int64 = MockDataType("int64", 8)
# triton_language.uint8 = MockDataType("uint8", 1)
# triton_language.uint16 = MockDataType("uint16", 2)
# triton_language.uint32 = MockDataType("uint32", 4)
# triton_language.uint64 = MockDataType("uint64", 8)
# triton_language.float16 = MockDataType("float16", 2)
# triton_language.float32 = MockDataType("float32", 4)
# triton_language.float64 = MockDataType("float64", 8)
# triton_language.bfloat16 = MockDataType("bfloat16", 2)

# # Math submodule
# triton_language_math = create_mock_module('triton.language.math', 'triton.language')
# triton_language_math.abs = MockTritonType("math.abs")
# triton_language_math.sin = MockTritonType("math.sin")
# triton_language_math.cos = MockTritonType("math.cos")
# triton_language_math.tan = MockTritonType("math.tan")
# triton_language_math.tanh = MockTritonType("math.tanh")
# triton_language_math.exp = MockTritonType("math.exp")
# triton_language_math.log = MockTritonType("math.log")
# triton_language_math.sqrt = MockTritonType("math.sqrt")

# triton_language.math = triton_language_math

# # Other modules
# triton_ops = create_mock_module('triton.ops', 'triton')
# triton_ops.matmul = MockTritonType("ops.matmul")

# triton_runtime = create_mock_module('triton.runtime', 'triton')
# triton_runtime.driver = create_mock_module('triton.runtime.driver', 'triton.runtime')
# triton_runtime.driver.active = create_mock_module('triton.runtime.driver.active', 'triton.runtime.driver')

# triton_testing = create_mock_module('triton.testing', 'triton')
# triton_testing.perf_report = MockTritonType("testing.perf_report")

# triton_compiler = create_mock_module('triton.compiler', 'triton')
# triton_compiler.compile = MockTritonType("compiler.compile")

# triton_heuristics = create_mock_module('triton.heuristics', 'triton')
# triton_heuristics.matmul = MockTritonType("heuristics.matmul")

# # Install all modules
# sys.modules['triton'] = triton_module
# sys.modules['triton.language'] = triton_language
# sys.modules['triton.language.math'] = triton_language_math
# sys.modules['triton.ops'] = triton_ops
# sys.modules['triton.runtime'] = triton_runtime
# sys.modules['triton.runtime.driver'] = triton_runtime.driver
# sys.modules['triton.runtime.driver.active'] = triton_runtime.driver.active
# sys.modules['triton.testing'] = triton_testing
# sys.modules['triton.compiler'] = triton_compiler
# sys.modules['triton.heuristics'] = triton_heuristics

# triton_language.__path__ = ['mock_triton_language']

# print("[Enhanced Mock] Triton modules with enhanced .value handling installed")










"""
Comprehensive mock triton module for Mac M3 Max compatibility
"""

import sys
import os
import torch
import warnings
from types import ModuleType
from importlib.machinery import ModuleSpec

def create_mock_module(name, parent_name=None):
    """Create a properly structured mock module"""
    module = ModuleType(name)
    
    # Create proper module spec
    spec = ModuleSpec(name, None)
    spec.origin = "mock"
    spec.submodule_search_locations = [] if parent_name else [f"mock_{name}"]
    module.__spec__ = spec
    module.__name__ = name
    module.__file__ = "<mock>"
    module.__package__ = parent_name if parent_name else name.split('.')[0]
    module.__path__ = [f"mock_{name}"] if not parent_name else []
    
    return module

# CRITICAL FIX: Create a wrapper for primitive types that handles .value
class ValueWrapper:
    """Wrapper for primitive types that provides .value attribute"""
    def __init__(self, value):
        self._value = value
    
    @property
    def value(self):
        return self._value
    
    def __getattr__(self, name):
        if name == 'value':
            return self._value
        # Try to get the attribute from the wrapped value
        if hasattr(self._value, name):
            return getattr(self._value, name)
        # If it doesn't exist, return a MockTritonType
        return MockTritonType(f"ValueWrapper({self._value}).{name}")
    
    def __call__(self, *args, **kwargs):
        if callable(self._value):
            return self._value(*args, **kwargs)
        return self._value
    
    def __str__(self):
        return str(self._value)
    
    def __repr__(self):
        return f"ValueWrapper({repr(self._value)})"
    
    def __int__(self):
        return int(self._value)
    
    def __float__(self):
        return float(self._value)
    
    def __bool__(self):
        return bool(self._value)
    
    def __eq__(self, other):
        if isinstance(other, ValueWrapper):
            return self._value == other._value
        return self._value == other
    
    def __hash__(self):
        return hash(self._value)

# Create a mock class that handles .value attribute access and function calls
class MockTritonType:
    """Mock class that can be used as both a callable and a type"""
    def __init__(self, name="MockTritonType", value=None):
        self.name = name
        self._value = value
        # CRITICAL FIX: Always ensure we have a value attribute
        if value is not None:
            self.value = value
        else:
            self.value = self  # Self-reference to handle .value access
    
    def __call__(self, *args, **kwargs):
        warnings.warn(f"Using mock {self.name} for Mac compatibility", UserWarning, stacklevel=2)
        return self
    
    def __getattr__(self, name):
        if name == 'value':
            return self._value if self._value is not None else self
        return MockTritonType(f"{self.name}.{name}")
    
    def __getitem__(self, item):
        return MockTritonType(f"{self.name}[{item}]")
    
    def __int__(self):
        return 0
    
    def __float__(self):
        return 0.0
    
    def __bool__(self):
        return True
    
    def __str__(self):
        return f"MockTritonType({self.name})"
    
    def __repr__(self):
        return f"<MockTritonType: {self.name}>"

# Mock data types that MUST have proper .value attribute
class MockDataType:
    """Mock data type that behaves like an enum with guaranteed .value attribute"""
    def __init__(self, name, size_bytes=4):
        self.name = name
        self.size_bytes = size_bytes
        # CRITICAL FIX: Always provide a .value attribute
        self.value = self  # Self-reference for enum-like behavior
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"MockDataType({self.name})"
    
    def __call__(self, *args, **kwargs):
        return self
    
    def __getattr__(self, name):
        # CRITICAL FIX: Always return self for .value access
        if name == 'value':
            return self
        return MockTritonType(f"{self.name}.{name}")
    
    def __int__(self):
        return self.size_bytes
    
    def __float__(self):
        return float(self.size_bytes)
    
    def __bool__(self):
        return True

# Mock triton functions
def mock_triton_jit(*args, **kwargs):
    """Mock triton.jit decorator"""
    def decorator(func):
        return func
    return decorator

def mock_triton_cdiv(a, b):
    """Mock ceiling division"""
    return (a + b - 1) // b

def mock_constexpr(value):
    """Mock constexpr function - CRITICAL FIX: Handle primitive types properly"""
    # CRITICAL FIX: Handle primitive types by wrapping them
    if isinstance(value, (int, float, str, bool)):
        return ValueWrapper(value)
    elif hasattr(value, 'value'):
        return value
    else:
        return ValueWrapper(value)

def mock_autotune(*args, **kwargs):
    """Mock autotune decorator"""
    def decorator(func):
        return func
    return decorator

def mock_next_power_of_2(x):
    """Mock next_power_of_2 function"""
    if x <= 0:
        return 1
    return 1 << (x - 1).bit_length()

def mock_config(*args, **kwargs):
    """Mock Config class"""
    class MockConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    return MockConfig(**kwargs)

def mock_heuristics(*args, **kwargs):
    """Mock heuristics function"""
    return MockTritonType("heuristics")

# CRITICAL FIX: Mock triton.testing functions
def mock_perf_report(*args, **kwargs):
    """Mock triton.testing.perf_report decorator"""
    def decorator(func):
        return func
    return decorator

def mock_do_bench(*args, **kwargs):
    """Mock triton.testing.do_bench function"""
    warnings.warn("Using mock triton.testing.do_bench for Mac compatibility", UserWarning, stacklevel=2)
    # Return a mock benchmark result
    return 1.0  # Mock execution time

def mock_assert_close(*args, **kwargs):
    """Mock triton.testing.assert_close function"""
    warnings.warn("Using mock triton.testing.assert_close for Mac compatibility", UserWarning, stacklevel=2)
    # Always pass assertions in mock mode
    return True

class MockBenchmark:
    """Mock benchmark class for triton.testing.Benchmark"""
    def __init__(self, *args, **kwargs):
        self.x_names = kwargs.get('x_names', [])
        self.x_vals = kwargs.get('x_vals', [])
        self.line_arg = kwargs.get('line_arg', 'provider')
        self.line_vals = kwargs.get('line_vals', [])
        self.line_names = kwargs.get('line_names', [])
        self.styles = kwargs.get('styles', [])
        self.ylabel = kwargs.get('ylabel', 'metric')
        self.plot_name = kwargs.get('plot_name', 'benchmark')
        self.args = kwargs.get('args', {})
    
    def __call__(self, func):
        """Make it work as a decorator"""
        return func
    
    def run(self, *args, **kwargs):
        """Mock run method"""
        return {"result": 1.0}

# Create main triton module
triton_module = create_mock_module('triton')
triton_module.jit = mock_triton_jit
triton_module.cdiv = mock_triton_cdiv
triton_module.next_power_of_2 = mock_next_power_of_2
triton_module.Config = mock_config
triton_module.autotune = mock_autotune
triton_module.heuristics = mock_heuristics
triton_module.__version__ = "2.1.0"

# Create triton.language module with ALL required attributes
triton_language = create_mock_module('triton.language', 'triton')

# CRITICAL: Add constexpr - this is what's missing and causing the error!
triton_language.constexpr = mock_constexpr

# Add all the standard triton.language attributes
triton_language.program_id = MockTritonType("program_id")
triton_language.num_programs = MockTritonType("num_programs")
triton_language.arange = MockTritonType("arange")
triton_language.load = MockTritonType("load")
triton_language.store = MockTritonType("store")
triton_language.atomic_add = MockTritonType("atomic_add")
triton_language.atomic_cas = MockTritonType("atomic_cas")
triton_language.atomic_xchg = MockTritonType("atomic_xchg")
triton_language.atomic_max = MockTritonType("atomic_max")
triton_language.atomic_min = MockTritonType("atomic_min")
triton_language.atomic_and = MockTritonType("atomic_and")
triton_language.atomic_or = MockTritonType("atomic_or")
triton_language.atomic_xor = MockTritonType("atomic_xor")
triton_language.dot = MockTritonType("dot")
triton_language.trans = MockTritonType("trans")
triton_language.broadcast_to = MockTritonType("broadcast_to")
triton_language.sum = MockTritonType("sum")
triton_language.max = MockTritonType("max")
triton_language.min = MockTritonType("min")
triton_language.maximum = MockTritonType("maximum")
triton_language.minimum = MockTritonType("minimum")
triton_language.where = MockTritonType("where")
triton_language.exp = MockTritonType("exp")
triton_language.exp2 = MockTritonType("exp2")
triton_language.log = MockTritonType("log")
triton_language.log2 = MockTritonType("log2")
triton_language.sqrt = MockTritonType("sqrt")
triton_language.rsqrt = MockTritonType("rsqrt")
triton_language.sin = MockTritonType("sin")
triton_language.cos = MockTritonType("cos")
triton_language.abs = MockTritonType("abs")
triton_language.pow = MockTritonType("pow")
triton_language.clamp = MockTritonType("clamp")

# CRITICAL FIX: Data types with GUARANTEED .value attribute - including bfloat16!
triton_language.int1 = MockDataType("int1", 1)
triton_language.int8 = MockDataType("int8", 1)
triton_language.int16 = MockDataType("int16", 2)
triton_language.int32 = MockDataType("int32", 4)
triton_language.int64 = MockDataType("int64", 8)
triton_language.uint8 = MockDataType("uint8", 1)
triton_language.uint16 = MockDataType("uint16", 2)
triton_language.uint32 = MockDataType("uint32", 4)
triton_language.uint64 = MockDataType("uint64", 8)
triton_language.float16 = MockDataType("float16", 2)
triton_language.float32 = MockDataType("float32", 4)
triton_language.float64 = MockDataType("float64", 8)
triton_language.bfloat16 = MockDataType("bfloat16", 2)  # CRITICAL: This was missing!

# Add additional FP8 data types that might be needed
triton_language.float8e4b15 = MockDataType("float8e4b15", 1)
triton_language.float8e4nv = MockDataType("float8e4nv", 1)
triton_language.float8e4b8 = MockDataType("float8e4b8", 1)
triton_language.float8e5 = MockDataType("float8e5", 1)
triton_language.float8e5b16 = MockDataType("float8e5b16", 1)
triton_language.float8e4m3fn = MockDataType("float8e4m3fn", 1)
triton_language.float8e5m2 = MockDataType("float8e5m2", 1)

# Additional functions
triton_language.zeros = MockTritonType("zeros")
triton_language.zeros_like = MockTritonType("zeros_like")
triton_language.full = MockTritonType("full")
triton_language.reshape = MockTritonType("reshape")
triton_language.view = MockTritonType("view")
triton_language.range = MockTritonType("range")
triton_language.reduce = MockTritonType("reduce")
triton_language.multiple_of = MockTritonType("multiple_of")
triton_language.static_print = MockTritonType("static_print")
triton_language.static_assert = MockTritonType("static_assert")
triton_language.device_print = MockTritonType("device_print")
triton_language.device_assert = MockTritonType("device_assert")
triton_language.debug_barrier = MockTritonType("debug_barrier")

# Math functions
triton_language.floor = MockTritonType("floor")
triton_language.ceil = MockTritonType("ceil")
triton_language.round = MockTritonType("round")
triton_language.trunc = MockTritonType("trunc")

# CRITICAL FIX: Create comprehensive triton.language.math submodule
triton_language_math = create_mock_module('triton.language.math', 'triton.language')

# All mathematical functions from triton.language.math
triton_language_math.abs = MockTritonType("math.abs")
triton_language_math.acos = MockTritonType("math.acos")
triton_language_math.acosh = MockTritonType("math.acosh")
triton_language_math.asin = MockTritonType("math.asin")
triton_language_math.asinh = MockTritonType("math.asinh")
triton_language_math.atan = MockTritonType("math.atan")
triton_language_math.atan2 = MockTritonType("math.atan2")
triton_language_math.atanh = MockTritonType("math.atanh")
triton_language_math.ceil = MockTritonType("math.ceil")
triton_language_math.clamp = MockTritonType("math.clamp")
triton_language_math.cos = MockTritonType("math.cos")
triton_language_math.cosh = MockTritonType("math.cosh")
triton_language_math.erf = MockTritonType("math.erf")
triton_language_math.erfc = MockTritonType("math.erfc")
triton_language_math.exp = MockTritonType("math.exp")
triton_language_math.exp2 = MockTritonType("math.exp2")
triton_language_math.expm1 = MockTritonType("math.expm1")
triton_language_math.fabs = MockTritonType("math.fabs")
triton_language_math.floor = MockTritonType("math.floor")
triton_language_math.fmod = MockTritonType("math.fmod")
triton_language_math.frexp = MockTritonType("math.frexp")
triton_language_math.gamma = MockTritonType("math.gamma")
triton_language_math.isfinite = MockTritonType("math.isfinite")
triton_language_math.isinf = MockTritonType("math.isinf")
triton_language_math.isnan = MockTritonType("math.isnan")
triton_language_math.j0 = MockTritonType("math.j0")
triton_language_math.j1 = MockTritonType("math.j1")
triton_language_math.ldexp = MockTritonType("math.ldexp")
triton_language_math.lgamma = MockTritonType("math.lgamma")
triton_language_math.log = MockTritonType("math.log")
triton_language_math.log10 = MockTritonType("math.log10")
triton_language_math.log1p = MockTritonType("math.log1p")
triton_language_math.log2 = MockTritonType("math.log2")
triton_language_math.logb = MockTritonType("math.logb")
triton_language_math.max = MockTritonType("math.max")
triton_language_math.min = MockTritonType("math.min")
triton_language_math.modf = MockTritonType("math.modf")
triton_language_math.nextafter = MockTritonType("math.nextafter")
triton_language_math.pow = MockTritonType("math.pow")
triton_language_math.remainder = MockTritonType("math.remainder")
triton_language_math.rint = MockTritonType("math.rint")
triton_language_math.round = MockTritonType("math.round")
triton_language_math.rsqrt = MockTritonType("math.rsqrt")
triton_language_math.scalb = MockTritonType("math.scalb")
triton_language_math.significand = MockTritonType("math.significand")
triton_language_math.sin = MockTritonType("math.sin")
triton_language_math.sinh = MockTritonType("math.sinh")
triton_language_math.sqrt = MockTritonType("math.sqrt")
triton_language_math.tan = MockTritonType("math.tan")
triton_language_math.tanh = MockTritonType("math.tanh")
triton_language_math.tgamma = MockTritonType("math.tgamma")
triton_language_math.trunc = MockTritonType("math.trunc")
triton_language_math.y0 = MockTritonType("math.y0")
triton_language_math.y1 = MockTritonType("math.y1")

# CRITICAL FIX: Add math submodule to triton.language
triton_language.math = triton_language_math

# CRITICAL FIX: Create comprehensive triton.language.extra submodule
triton_language_extra = create_mock_module('triton.language.extra', 'triton.language')

# Add common extra functions that VILA might need
triton_language_extra.cuda = create_mock_module('triton.language.extra.cuda', 'triton.language.extra')
triton_language_extra.hip = create_mock_module('triton.language.extra.hip', 'triton.language.extra')
triton_language_extra.libdevice = MockTritonType("extra.libdevice")
triton_language_extra.tma = MockTritonType("extra.tma")
triton_language_extra.experimental = MockTritonType("extra.experimental")
triton_language_extra.fp8 = MockTritonType("extra.fp8")
triton_language_extra.block_advance = MockTritonType("extra.block_advance")
triton_language_extra.block_load = MockTritonType("extra.block_load")
triton_language_extra.block_store = MockTritonType("extra.block_store")
triton_language_extra.block_copy = MockTritonType("extra.block_copy")
triton_language_extra.block_reduce = MockTritonType("extra.block_reduce")
triton_language_extra.block_scan = MockTritonType("extra.block_scan")
triton_language_extra.warp_reduce = MockTritonType("extra.warp_reduce")
triton_language_extra.warp_scan = MockTritonType("extra.warp_scan")
triton_language_extra.shared_memory = MockTritonType("extra.shared_memory")
triton_language_extra.barrier = MockTritonType("extra.barrier")
triton_language_extra.memory_fence = MockTritonType("extra.memory_fence")
triton_language_extra.fence = MockTritonType("extra.fence")
triton_language_extra.grid_size = MockTritonType("extra.grid_size")
triton_language_extra.block_size = MockTritonType("extra.block_size")
triton_language_extra.thread_id = MockTritonType("extra.thread_id")
triton_language_extra.block_id = MockTritonType("extra.block_id")
triton_language_extra.grid_id = MockTritonType("extra.grid_id")

# Add CUDA-specific functions to triton.language.extra.cuda
triton_language_extra_cuda = triton_language_extra.cuda

# Add libdevice to CUDA submodule (this is what VILA is looking for)
triton_language_extra_cuda.libdevice = MockTritonType("extra.cuda.libdevice")

# Add other CUDA-specific functions
triton_language_extra_cuda.blockIdx = MockTritonType("extra.cuda.blockIdx")
triton_language_extra_cuda.blockDim = MockTritonType("extra.cuda.blockDim")
triton_language_extra_cuda.threadIdx = MockTritonType("extra.cuda.threadIdx")
triton_language_extra_cuda.gridDim = MockTritonType("extra.cuda.gridDim")
triton_language_extra_cuda.warpSize = MockTritonType("extra.cuda.warpSize")
triton_language_extra_cuda.syncthreads = MockTritonType("extra.cuda.syncthreads")
triton_language_extra_cuda.threadfence = MockTritonType("extra.cuda.threadfence")
triton_language_extra_cuda.threadfence_block = MockTritonType("extra.cuda.threadfence_block")
triton_language_extra_cuda.threadfence_system = MockTritonType("extra.cuda.threadfence_system")
triton_language_extra_cuda.shfl = MockTritonType("extra.cuda.shfl")
triton_language_extra_cuda.shfl_up = MockTritonType("extra.cuda.shfl_up")
triton_language_extra_cuda.shfl_down = MockTritonType("extra.cuda.shfl_down")
triton_language_extra_cuda.shfl_xor = MockTritonType("extra.cuda.shfl_xor")
triton_language_extra_cuda.ballot = MockTritonType("extra.cuda.ballot")
triton_language_extra_cuda.any = MockTritonType("extra.cuda.any")
triton_language_extra_cuda.all = MockTritonType("extra.cuda.all")
triton_language_extra_cuda.popc = MockTritonType("extra.cuda.popc")
triton_language_extra_cuda.clz = MockTritonType("extra.cuda.clz")
triton_language_extra_cuda.ffs = MockTritonType("extra.cuda.ffs")
triton_language_extra_cuda.brev = MockTritonType("extra.cuda.brev")
triton_language_extra_cuda.fma = MockTritonType("extra.cuda.fma")
triton_language_extra_cuda.mad = MockTritonType("extra.cuda.mad")

# Add to triton.language
triton_language.extra = triton_language_extra

# Create triton.ops module
triton_ops = create_mock_module('triton.ops', 'triton')
triton_ops.matmul = MockTritonType("ops.matmul")
triton_ops.addmm = MockTritonType("ops.addmm")
triton_ops.conv = MockTritonType("ops.conv")
triton_ops.flash_attention = MockTritonType("ops.flash_attention")

# Create triton.runtime module and submodules
triton_runtime = create_mock_module('triton.runtime', 'triton')
triton_runtime.driver = create_mock_module('triton.runtime.driver', 'triton.runtime')
triton_runtime.driver.active = create_mock_module('triton.runtime.driver.active', 'triton.runtime.driver')

# Create triton.runtime.autotuner module
triton_runtime_autotuner = create_mock_module('triton.runtime.autotuner', 'triton.runtime')
triton_runtime_autotuner.Autotuner = MockTritonType("autotuner.Autotuner")
triton_runtime_autotuner.Config = MockTritonType("autotuner.Config")
triton_runtime_autotuner.Heuristics = MockTritonType("autotuner.Heuristics")
triton_runtime_autotuner.autotune = mock_autotune
triton_runtime_autotuner.heuristics = mock_heuristics

# Create triton.runtime.jit module
triton_runtime_jit = create_mock_module('triton.runtime.jit', 'triton.runtime')
triton_runtime_jit.JITFunction = MockTritonType("jit.JITFunction")
triton_runtime_jit.KernelInterface = MockTritonType("jit.KernelInterface")
triton_runtime_jit.MockTensor = MockTritonType("jit.MockTensor")
triton_runtime_jit.TensorWrapper = MockTritonType("jit.TensorWrapper")
triton_runtime_jit.reinterpret = MockTritonType("jit.reinterpret")

# Create triton.runtime.cache module
triton_runtime_cache = create_mock_module('triton.runtime.cache', 'triton.runtime')
triton_runtime_cache.get_cache_manager = MockTritonType("cache.get_cache_manager")
triton_runtime_cache.get_dump_manager = MockTritonType("cache.get_dump_manager")

# Create triton.runtime.errors module
triton_runtime_errors = create_mock_module('triton.runtime.errors', 'triton.runtime')
triton_runtime_errors.OutOfResources = MockTritonType("errors.OutOfResources")
triton_runtime_errors.InterpreterError = MockTritonType("errors.InterpreterError")

# CRITICAL FIX: Create triton.testing module
triton_testing = create_mock_module('triton.testing', 'triton')
triton_testing.perf_report = mock_perf_report
triton_testing.do_bench = mock_do_bench
triton_testing.assert_close = mock_assert_close
triton_testing.Benchmark = MockBenchmark

# Create triton.compiler module
triton_compiler = create_mock_module('triton.compiler', 'triton')
triton_compiler.compile = MockTritonType("compiler.compile")
triton_compiler.CompiledKernel = MockTritonType("compiler.CompiledKernel")

# Create triton.heuristics module
triton_heuristics = create_mock_module('triton.heuristics', 'triton')
triton_heuristics.matmul = MockTritonType("heuristics.matmul")
triton_heuristics.addmm = MockTritonType("heuristics.addmm")

# Create triton.profiler module
triton_profiler = create_mock_module('triton.profiler', 'triton')
triton_profiler.profile = MockTritonType("profiler.profile")
triton_profiler.Profiler = MockTritonType("profiler.Profiler")

# CRITICAL FIX: Install all triton mock modules including triton.testing
sys.modules['triton'] = triton_module
sys.modules['triton.language'] = triton_language
sys.modules['triton.language.math'] = triton_language_math
sys.modules['triton.language.extra'] = triton_language_extra
sys.modules['triton.language.extra.cuda'] = triton_language_extra_cuda
sys.modules['triton.ops'] = triton_ops
sys.modules['triton.runtime'] = triton_runtime
sys.modules['triton.runtime.driver'] = triton_runtime.driver
sys.modules['triton.runtime.driver.active'] = triton_runtime.driver.active
sys.modules['triton.runtime.autotuner'] = triton_runtime_autotuner
sys.modules['triton.runtime.jit'] = triton_runtime_jit
sys.modules['triton.runtime.cache'] = triton_runtime_cache
sys.modules['triton.runtime.errors'] = triton_runtime_errors
sys.modules['triton.testing'] = triton_testing  # CRITICAL FIX: Add this line
sys.modules['triton.compiler'] = triton_compiler
sys.modules['triton.heuristics'] = triton_heuristics
sys.modules['triton.profiler'] = triton_profiler

# Make sure triton.language is recognized as a package
triton_language.__path__ = ['mock_triton_language']

# CRITICAL FIX: Add testing attribute to main triton module
triton_module.testing = triton_testing

print("[Mock] Triton module installed for Mac compatibility")
print("[Mock] - Added missing constexpr function")
print("[Mock] - All triton.language attributes available")
print("[Mock] - VILA compatibility improved")
print("[Mock] - CRITICAL FIX: Added triton.language.math submodule")
print("[Mock] - CRITICAL FIX: Added triton.language.extra submodule")
print("[Mock] - CRITICAL FIX: Added triton.language.extra.cuda submodule")
print("[Mock] - CRITICAL FIX: Added libdevice to triton.language.extra.cuda")
print("[Mock] - CRITICAL FIX: Added triton.testing module with perf_report, do_bench, assert_close")
print("[Mock] - CRITICAL FIX: Added triton.testing.Benchmark class")
print("[Mock] - CRITICAL FIX: Fixed constexpr to handle primitive types properly")
print("[Mock] - CRITICAL FIX: Enhanced MockDataType to always have .value attribute")
print("[Mock] - CRITICAL FIX: Added missing bfloat16 data type")
print("[Mock] - CRITICAL FIX: Removed problematic built-in type patching")












# """
# Enhanced mock triton module with callable support and proper specs
# """

# import sys
# import os
# from types import ModuleType
# from importlib.machinery import ModuleSpec
# import warnings

# class CallableModuleType(ModuleType):
#     """A module that can be called as a function"""
#     def __init__(self, name):
#         super().__init__(name)
#         self.__name__ = name
#         self.__file__ = "<callable_mock>"
#         self.__package__ = name.split('.')[0] if '.' in name else name
    
#     def __call__(self, *args, **kwargs):
#         """Make the module callable"""
#         warnings.warn(f"Using callable mock for {self.__name__}", UserWarning, stacklevel=2)
#         return self
    
#     def __getattr__(self, name):
#         """Return callable sub-modules"""
#         submodule_name = f"{self.__name__}.{name}"
#         return CallableModuleType(submodule_name)

# def create_mock_module(name, parent_name=None):
#     """Create a properly structured mock module that's callable"""
#     module = CallableModuleType(name)
    
#     # CRITICAL FIX: Create proper module spec
#     spec = ModuleSpec(name, None)
#     spec.origin = "mock"
#     spec.submodule_search_locations = [] if parent_name else [f"mock_{name}"]
#     module.__spec__ = spec
#     module.__name__ = name
#     module.__file__ = "<mock>"
#     module.__package__ = parent_name if parent_name else name.split('.')[0]
#     module.__path__ = [f"mock_{name}"] if not parent_name else []
    
#     return module

# # Enhanced mock class with better .value handling
# class MockTritonType:
#     """Mock class that can be used as both a callable and a type"""
#     def __init__(self, name="MockTritonType", value=None):
#         self.name = name
#         self._value = value
#         # Make sure we have a proper value attribute
#         if hasattr(self, '__dict__'):
#             self.__dict__['value'] = value if value is not None else self
    
#     def __call__(self, *args, **kwargs):
#         warnings.warn(f"Using mock {self.name} for Mac compatibility", UserWarning, stacklevel=2)
#         return self
    
#     def __getattr__(self, name):
#         if name == 'value':
#             return self._value if self._value is not None else self
#         return MockTritonType(f"{self.name}.{name}")
    
#     @property
#     def value(self):
#         """Handle .value attribute access"""
#         return self._value if self._value is not None else self
    
#     def __getitem__(self, item):
#         return MockTritonType(f"{self.name}[{item}]")
    
#     def __int__(self):
#         return 0
    
#     def __float__(self):
#         return 0.0
    
#     def __bool__(self):
#         return True
    
#     def __str__(self):
#         return f"MockTritonType({self.name})"
    
#     def __repr__(self):
#         return f"<MockTritonType: {self.name}>"

# # Mock triton functions
# def mock_triton_jit(*args, **kwargs):
#     def decorator(func):
#         return func
#     return decorator

# def mock_triton_cdiv(a, b):
#     return (a + b - 1) // b

# def mock_constexpr(value):
#     return value

# def mock_autotune(*args, **kwargs):
#     def decorator(func):
#         return func
#     return decorator

# def mock_next_power_of_2(x):
#     if x <= 0:
#         return 1
#     return 1 << (x - 1).bit_length()

# def mock_config(*args, **kwargs):
#     class MockConfig:
#         def __init__(self, **kwargs):
#             for k, v in kwargs.items():
#                 setattr(self, k, v)
#     return MockConfig(**kwargs)

# # Create main triton module with proper spec
# triton_module = create_mock_module('triton')

# # Add mock functions
# triton_module.jit = mock_triton_jit
# triton_module.cdiv = mock_triton_cdiv
# triton_module.next_power_of_2 = mock_next_power_of_2
# triton_module.Config = mock_config
# triton_module.autotune = mock_autotune
# triton_module.__version__ = "2.1.0"

# # Create triton.language as a callable package
# triton_language = create_mock_module('triton.language', 'triton')

# # Add basic triton.language functions
# triton_language.program_id = MockTritonType("program_id")
# triton_language.arange = MockTritonType("arange")
# triton_language.load = MockTritonType("load")
# triton_language.store = MockTritonType("store")
# triton_language.exp = MockTritonType("exp")
# triton_language.log = MockTritonType("log")
# triton_language.sin = MockTritonType("sin")
# triton_language.cos = MockTritonType("cos")
# triton_language.tan = MockTritonType("tan")
# triton_language.tanh = MockTritonType("tanh")
# triton_language.constexpr = mock_constexpr

# # Add data types
# triton_language.int32 = MockTritonType("int32")
# triton_language.float32 = MockTritonType("float32")
# triton_language.float16 = MockTritonType("float16")

# # Create math submodule
# triton_language_math = create_mock_module('triton.language.math', 'triton.language')
# triton_language_math.tanh = MockTritonType("math.tanh")
# triton_language_math.tan = MockTritonType("math.tan")
# triton_language_math.sin = MockTritonType("math.sin")
# triton_language_math.cos = MockTritonType("math.cos")

# triton_language.math = triton_language_math

# # Install modules
# sys.modules['triton'] = triton_module
# sys.modules['triton.language'] = triton_language
# sys.modules['triton.language.math'] = triton_language_math

# print("[Mock Final] Enhanced triton mock with callable modules installed")
# print("[Mock Final] - All modules are now callable")
# print("[Mock Final] - Fixed 'module' object is not callable errors")
# print("[Mock Final] - CRITICAL: Fixed triton.__spec__ is None error")












# """
# Comprehensive triton mock based on actual triton source structure
# """

# import sys
# import os
# from types import ModuleType
# from importlib.machinery import ModuleSpec
# import warnings

# def create_mock_module(name, parent_name=None):
#     """Create a properly structured mock module"""
#     module = ModuleType(name)
    
#     # Create proper module spec
#     spec = ModuleSpec(name, None)
#     spec.origin = "mock"
#     spec.submodule_search_locations = [] if parent_name else [f"mock_{name}"]
#     module.__spec__ = spec
#     module.__name__ = name
#     module.__file__ = "<mock>"
#     module.__package__ = parent_name if parent_name else name.split('.')[0]
#     module.__path__ = [f"mock_{name}"] if not parent_name else []
    
#     return module

# # Enhanced MockTritonType that handles all edge cases
# class MockTritonType:
#     """Mock class that can be used as both a callable and a type"""
#     def __init__(self, name="MockTritonType", return_value=None):
#         self.name = name
#         self._return_value = return_value if return_value is not None else self
#         # Explicitly set value
#         object.__setattr__(self, 'value', self._return_value)
    
#     def __getattr__(self, name):
#         if name == 'value':
#             return self._return_value
#         return MockTritonType(f"{self.name}.{name}")
    
#     def __call__(self, *args, **kwargs):
#         warnings.warn(f"Using mock {self.name} for Mac compatibility", UserWarning, stacklevel=2)
#         return self._return_value
    
#     def __getitem__(self, item):
#         return MockTritonType(f"{self.name}[{item}]")
    
#     def __int__(self):
#         return 0
    
#     def __float__(self):
#         return 0.0
    
#     def __bool__(self):
#         return True
    
#     def __str__(self):
#         return f"MockTritonType({self.name})"
    
#     def __repr__(self):
#         return f"<MockTritonType: {self.name}>"

# # Enhanced data type mock
# class MockDataType:
#     """Mock data type that behaves like an enum"""
#     def __init__(self, name, size_bytes=4):
#         self.name = name
#         self.size_bytes = size_bytes
#         # Set value to self for enum-like behavior
#         object.__setattr__(self, 'value', self)
    
#     def __getattr__(self, name):
#         if name == 'value':
#             return self
#         return MockTritonType(f"{self.name}.{name}")
    
#     def __call__(self, *args, **kwargs):
#         return self
    
#     def __str__(self):
#         return self.name
    
#     def __repr__(self):
#         return f"MockDataType({self.name})"
    
#     def __int__(self):
#         return self.size_bytes
    
#     def __float__(self):
#         return float(self.size_bytes)

# # Safe constexpr that wraps values properly
# def safe_constexpr(value):
#     """Safe constexpr implementation that handles .value access"""
#     class SafeConstExpr:
#         def __init__(self, val):
#             self.val = val
#             object.__setattr__(self, 'value', val)
        
#         def __getattr__(self, name):
#             if name == 'value':
#                 return self.val
#             return getattr(self.val, name, MockTritonType(f"constexpr.{name}"))
        
#         def __call__(self, *args, **kwargs):
#             return self.val
        
#         def __int__(self):
#             try:
#                 return int(self.val)
#             except (ValueError, TypeError):
#                 return 0
        
#         def __float__(self):
#             try:
#                 return float(self.val)
#             except (ValueError, TypeError):
#                 return 0.0
        
#         def __str__(self):
#             return str(self.val)
        
#         def __repr__(self):
#             return f"SafeConstExpr({self.val})"
    
#     return SafeConstExpr(value)

# # Mock functions
# def mock_triton_jit(*args, **kwargs):
#     def decorator(func):
#         return func
#     return decorator

# def mock_triton_cdiv(a, b):
#     return (a + b - 1) // b

# def mock_autotune(*args, **kwargs):
#     def decorator(func):
#         return func
#     return decorator

# def mock_next_power_of_2(x):
#     if x <= 0:
#         return 1
#     return 1 << (x - 1).bit_length()

# def mock_config(*args, **kwargs):
#     """Fixed mock config that handles both positional and keyword arguments"""
#     class MockConfig:
#         def __init__(self, *args, **kwargs):
#             # Handle positional arguments
#             if args:
#                 # Common pattern: Config({key: value, ...})
#                 if len(args) == 1 and isinstance(args[0], dict):
#                     for k, v in args[0].items():
#                         setattr(self, k, v)
#                 else:
#                     # Store positional args as attributes
#                     for i, arg in enumerate(args):
#                         setattr(self, f'arg_{i}', arg)
            
#             # Handle keyword arguments
#             for k, v in kwargs.items():
#                 setattr(self, k, v)
        
#         def __getattr__(self, name):
#             return MockTritonType(f"config.{name}")
        
#         def __repr__(self):
#             return f"MockConfig({self.__dict__})"
    
#     return MockConfig(*args, **kwargs)

# def mock_heuristics(*args, **kwargs):
#     return MockTritonType("heuristics")

# # Create main triton module
# triton_module = create_mock_module('triton')
# triton_module.jit = mock_triton_jit
# triton_module.cdiv = mock_triton_cdiv
# triton_module.next_power_of_2 = mock_next_power_of_2
# triton_module.Config = mock_config
# triton_module.autotune = mock_autotune
# triton_module.heuristics = mock_heuristics
# triton_module.__version__ = "2.1.0"

# # Create triton.language module
# triton_language = create_mock_module('triton.language', 'triton')
# triton_language.constexpr = safe_constexpr

# # Add all language functions
# language_functions = [
#     'program_id', 'num_programs', 'arange', 'load', 'store', 'atomic_add',
#     'atomic_cas', 'atomic_xchg', 'atomic_max', 'atomic_min', 'atomic_and',
#     'atomic_or', 'atomic_xor', 'dot', 'dot_scaled', 'trans', 'broadcast_to',
#     'sum', 'max', 'min', 'maximum', 'minimum', 'where', 'exp', 'exp2',
#     'log', 'log2', 'log10', 'sqrt', 'rsqrt', 'sin', 'cos', 'tan', 'asin',
#     'acos', 'atan', 'atan2', 'sinh', 'cosh', 'tanh', 'asinh', 'acosh',
#     'atanh', 'floor', 'ceil', 'round', 'trunc', 'fmod', 'remainder', 'abs',
#     'pow', 'clamp', 'multiple_of', 'max_constancy', 'max_contiguous',
#     'static_print', 'static_assert', 'static_range', 'device_print',
#     'device_assert', 'debug_barrier', 'zeros', 'zeros_like', 'full',
#     'full_like', 'reshape', 'view', 'permute', 'transpose', 'expand_dims',
#     'squeeze', 'ravel', 'range', 'reduce', 'slice', 'split', 'join', 'cat',
#     'gather', 'scatter', 'histogram', 'make_block_ptr', 'advance',
#     'inline_asm_elementwise', 'dtype', 'tensor', 'tuple', 'tuple_type',
#     'pointer_type', 'pi32_t', 'semantic'
# ]

# for func_name in language_functions:
#     setattr(triton_language, func_name, MockTritonType(func_name))

# # Add data types with proper .value handling
# data_types = [
#     ('int1', 1), ('int8', 1), ('int16', 2), ('int32', 4), ('int64', 8),
#     ('uint8', 1), ('uint16', 2), ('uint32', 4), ('uint64', 8),
#     ('float16', 2), ('float32', 4), ('float64', 8), ('bfloat16', 2),
#     ('float8e4b15', 1), ('float8e4nv', 1), ('float8e4b8', 1),
#     ('float8e5', 1), ('float8e5b16', 1), ('float8e4m3fn', 1), ('float8e5m2', 1)
# ]

# for dtype_name, size in data_types:
#     setattr(triton_language, dtype_name, MockDataType(dtype_name, size))

# # Create triton.language.math module
# triton_language_math = create_mock_module('triton.language.math', 'triton.language')
# math_functions = [
#     'abs', 'acos', 'acosh', 'asin', 'asinh', 'atan', 'atan2', 'atanh',
#     'ceil', 'clamp', 'cos', 'cosh', 'erf', 'erfc', 'exp', 'exp2', 'expm1',
#     'fabs', 'floor', 'fmod', 'frexp', 'gamma', 'isfinite', 'isinf', 'isnan',
#     'j0', 'j1', 'ldexp', 'lgamma', 'log', 'log10', 'log1p', 'log2', 'logb',
#     'modf', 'nearbyint', 'nextafter', 'pow', 'remainder', 'rint', 'round',
#     'rsqrt', 'scalb', 'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'tgamma',
#     'trunc', 'y0', 'y1'
# ]

# for func_name in math_functions:
#     setattr(triton_language_math, func_name, MockTritonType(f"math.{func_name}"))

# triton_language.math = triton_language_math

# # Create triton.language.extra module
# triton_language_extra = create_mock_module('triton.language.extra', 'triton.language')

# # Add common extra functions
# extra_functions = [
#     'cuda', 'hip', 'libdevice', 'tma', 'experimental', 'fp8', 'block_advance',
#     'block_load', 'block_store', 'block_copy', 'block_reduce', 'block_scan',
#     'warp_reduce', 'warp_scan', 'shared_memory', 'barrier', 'memory_fence',
#     'fence', 'grid_size', 'block_size', 'thread_id', 'block_id', 'grid_id',
#     'cooperative_groups', 'shuffle', 'ballot', 'any', 'all', 'popcount',
#     'clz', 'ctz', 'brev', 'popc', 'ffs', 'fls', 'bfe', 'bfi', 'prmt',
#     'pack', 'unpack', 'ldg', 'ldcg', 'ldcs', 'ldlu', 'ldcv', 'ldu',
#     'stg', 'stcg', 'stcs', 'stlu', 'stcv', 'stu', 'shfl', 'shfl_up',
#     'shfl_down', 'shfl_xor', 'match_any', 'match_all', 'activemask',
#     'coalesced_groups', 'labeled_partition', 'binary_partition',
#     'this_thread_block', 'thread_block_tile', 'sync', 'memcpy_async',
#     'cp_async', 'cp_async_wait', 'cp_async_commit', 'cp_async_bulk',
#     'mbarrier', 'arrive', 'wait', 'expect_tx', 'cuda_memcpy_async',
#     'cuda_barrier', 'cuda_fence', 'cuda_syncthreads', 'cuda_threadfence',
#     'cuda_threadfence_block', 'cuda_threadfence_system'
# ]

# for func_name in extra_functions:
#     setattr(triton_language_extra, func_name, MockTritonType(f"extra.{func_name}"))

# # Create triton.language.extra.cuda module
# triton_language_extra_cuda = create_mock_module('triton.language.extra.cuda', 'triton.language.extra')

# # Add CUDA-specific functions INCLUDING libdevice
# cuda_functions = [
#     'libdevice',
#     'blockIdx', 'blockDim', 'threadIdx', 'gridDim', 'warpSize',
#     'syncthreads', 'threadfence', 'threadfence_block', 'threadfence_system',
#     'shfl', 'shfl_up', 'shfl_down', 'shfl_xor', 'ballot', 'any', 'all',
#     'popc', 'clz', 'ffs', 'brev', 'fma', 'mad', 'tex1D', 'tex2D', 'tex3D',
#     'surf1Dwrite', 'surf2Dwrite', 'surf3Dwrite', 'surf1Dread', 'surf2Dread',
#     'surf3Dread', 'clock', 'clock64', 'nanosleep', 'ldg', 'ldcg', 'ldcs',
#     'ldlu', 'ldcv', 'ldu', 'stg', 'stcg', 'stcs', 'stlu', 'stcv', 'stu',
#     'memcpy_async', 'cp_async', 'cp_async_wait', 'cp_async_commit',
#     'cp_async_bulk', 'mbarrier', 'arrive', 'wait', 'expect_tx',
#     'cuda_memcpy_async', 'cuda_barrier', 'cuda_fence', 'cuda_syncthreads',
#     'cuda_threadfence', 'cuda_threadfence_block', 'cuda_threadfence_system',
#     'activemask', 'lanemask_eq', 'lanemask_le', 'lanemask_lt', 'lanemask_ge',
#     'lanemask_gt', 'match_any', 'match_all', 'coalesced_groups',
#     'labeled_partition', 'binary_partition', 'this_thread_block',
#     'thread_block_tile', 'sync', 'reduce', 'scan', 'shuffle', 'vote',
#     'cooperative_groups', 'wmma', 'mma', 'ldmatrix', 'stmatrix', 'tma_load',
#     'tma_store', 'tma_fence', 'tensor_map', 'cluster_group', 'cluster_barrier',
#     'cluster_sync', 'cluster_arrive', 'cluster_wait', 'distributed_shared_memory',
#     'remote_barrier', 'async_copy', 'async_copy_wait', 'async_copy_commit'
# ]

# for func_name in cuda_functions:
#     setattr(triton_language_extra_cuda, func_name, MockTritonType(f"extra.cuda.{func_name}"))

# # Add cuda submodule to extra
# triton_language_extra.cuda = triton_language_extra_cuda

# # Add extra to triton.language
# triton_language.extra = triton_language_extra

# # Create comprehensive triton modules based on source analysis
# triton_modules = {
#     'triton.ops': ['matmul', 'addmm', 'conv', 'flash_attention'],
#     'triton.runtime': [],
#     'triton.runtime.driver': [],
#     'triton.runtime.driver.active': [],
#     'triton.runtime.autotuner': ['Autotuner', 'Config', 'Heuristics', 'autotune', 'heuristics'],
#     'triton.runtime.jit': ['JITFunction', 'KernelInterface', 'MockTensor', 'TensorWrapper', 'reinterpret'],
#     'triton.runtime.cache': ['get_cache_manager', 'get_dump_manager', 'get_override_manager', 'get_cache_key'],
#     'triton.runtime.errors': ['OutOfResources', 'InterpreterError'],
#     'triton.testing': ['perf_report', 'do_bench', 'assert_close'],
#     'triton.compiler': ['compile', 'CompiledKernel', 'ASTSource'],
#     'triton.compiler.compiler': ['compile', 'CompiledKernel', 'ASTSource'],
#     'triton.heuristics': ['matmul', 'addmm'],
#     'triton.profiler': ['profile', 'Profiler'],
#     'triton.tools': ['getBoolEnv', 'getStrEnv'],
#     'triton.backends': ['backends'],
#     'triton.backends.compiler': ['BaseBackend', 'GPUTarget', 'Language'],
#     'triton._C': ['libtriton'],
#     'triton._C.libtriton': ['get_cache_invalidating_env_vars', 'ir'],
#     'triton.knobs': ['nvidia'],
#     'triton.knobs.nvidia': ['ptxas'],
#     'triton.knobs.nvidia.ptxas': ['version'],
#     'triton.common': ['common_functions'],
#     'triton_kernels': ['routing', 'matmul_ogs', 'tensor', 'numerics'],
#     'triton_kernels.routing': ['routing'],
#     'triton_kernels.matmul_ogs': ['matmul_ogs', 'PrecisionConfig', 'FlexCtx', 'FnSpecs', 'FusedActivation'],
#     'triton_kernels.tensor': ['wrap_torch_tensor', 'FP4', 'convert_layout'],
#     'triton_kernels.numerics': ['InFlexData', 'OutFlexData'],
#     'triton_kernels.target_info': ['is_cuda', 'is_hip', 'get_cdna_version'],
# }

# # Create all the modules
# created_modules = {
#     'triton': triton_module,
#     'triton.language': triton_language,
#     'triton.language.math': triton_language_math,
#     'triton.language.extra': triton_language_extra,
#     'triton.language.extra.cuda': triton_language_extra_cuda,
# }

# for module_name, attrs in triton_modules.items():
#     parts = module_name.split('.')
#     parent_name = '.'.join(parts[:-1]) if len(parts) > 1 else None
    
#     module = create_mock_module(module_name, parent_name)
    
#     # Add attributes/functions to the module
#     for attr_name in attrs:
#         if attr_name in ['Config', 'autotune', 'heuristics'] and module_name == 'triton.runtime.autotuner':
#             # Use the same functions as main triton module
#             setattr(module, attr_name, getattr(triton_module, attr_name))
#         else:
#             setattr(module, attr_name, MockTritonType(f"{module_name}.{attr_name}"))
    
#     created_modules[module_name] = module

# # CRITICAL FIX: Add submodules as attributes to their parent modules
# # This is what was missing - VILA expects triton.testing to exist as an attribute

# # Add language to main triton module
# triton_module.language = triton_language

# # Add all submodules to their parent modules
# for module_name, module in created_modules.items():
#     if '.' in module_name:
#         parts = module_name.split('.')
#         parent_name = '.'.join(parts[:-1])
#         child_name = parts[-1]
        
#         if parent_name in created_modules:
#             parent_module = created_modules[parent_name]
#             setattr(parent_module, child_name, module)

# # Install all modules
# for module_name, module in created_modules.items():
#     sys.modules[module_name] = module

# # Make sure triton.language is recognized as a package
# triton_language.__path__ = ['mock_triton_language']
# triton_language_extra.__path__ = ['mock_triton_language_extra']

# # Special handling for specific modules that need special setup
# if 'triton.knobs.nvidia.ptxas' in sys.modules:
#     sys.modules['triton.knobs.nvidia.ptxas'].version = "12.3"

# print("[Mock Final] Enhanced triton mock with all submodule attributes installed")
# print("[Mock Final] - All triton modules with proper .value handling")
# print("[Mock Final] - Fixed Config() to handle both positional and keyword args")
# print("[Mock Final] - Enhanced data type mocks")
# print("[Mock Final] - Complete math module")
# print("[Mock Final] - Added triton.language.extra module")
# print("[Mock Final] - Added triton.language.extra.cuda module")
# print("[Mock Final] - Added libdevice to triton.language.extra.cuda")
# print("[Mock Final] - Added triton.common module")
# print("[Mock Final] - Added triton_kernels modules")
# print("[Mock Final] - Added all compiler and backend modules")
# print("[Mock Final] - FIXED: Added all submodules as attributes to parent modules")
# print("[Mock Final] - triton.testing is now available as triton.testing")





























# """
# Final comprehensive triton mock that handles the .value attribute issue
# """

# import sys
# import os
# from types import ModuleType
# from importlib.machinery import ModuleSpec
# import warnings

# # Create a completely robust mock that handles all edge cases
# class RobustMockTritonType:
#     """Ultra-robust mock that handles all possible attribute access patterns"""
    
#     def __init__(self, name="RobustMockTritonType", mock_value=None):
#         self.name = name
#         self._mock_value = mock_value if mock_value is not None else self
        
#         # Pre-populate common attributes to avoid AttributeError
#         self.value = self._mock_value
#         self.dtype = self._mock_value
#         self.shape = ()
#         self.ndim = 0
#         self.size = 1
    
#     def __getattr__(self, name):
#         """Handle any attribute access gracefully"""
#         if name == 'value':
#             return self._mock_value
#         elif name in ['dtype', 'shape', 'ndim', 'size']:
#             return getattr(self, name, self._mock_value)
#         else:
#             return RobustMockTritonType(f"{self.name}.{name}")
    
#     def __setattr__(self, name, value):
#         """Allow setting attributes"""
#         if name in ['name', '_mock_value']:
#             super().__setattr__(name, value)
#         else:
#             # For other attributes, set them normally
#             super().__setattr__(name, value)
    
#     def __call__(self, *args, **kwargs):
#         """Handle function calls"""
#         return self._mock_value
    
#     def __getitem__(self, item):
#         """Handle indexing"""
#         return RobustMockTritonType(f"{self.name}[{item}]")
    
#     def __setitem__(self, key, value):
#         """Handle item assignment"""
#         pass
    
#     def __int__(self):
#         return 0
    
#     def __float__(self):
#         return 0.0
    
#     def __bool__(self):
#         return True
    
#     def __len__(self):
#         return 1
    
#     def __iter__(self):
#         return iter([self])
    
#     def __str__(self):
#         return f"RobustMockTritonType({self.name})"
    
#     def __repr__(self):
#         return f"<RobustMockTritonType: {self.name}>"
    
#     def __eq__(self, other):
#         return True
    
#     def __ne__(self, other):
#         return False
    
#     def __lt__(self, other):
#         return False
    
#     def __le__(self, other):
#         return True
    
#     def __gt__(self, other):
#         return False
    
#     def __ge__(self, other):
#         return True

# # Enhanced data type that's guaranteed to work
# class EnhancedMockDataType(RobustMockTritonType):
#     """Enhanced data type that handles all enum-like access patterns"""
    
#     def __init__(self, name, size_bytes=4):
#         super().__init__(name)
#         self.name = name
#         self.size_bytes = size_bytes
        
#         # Set value to self (enum-like behavior)
#         self.value = self
#         self._mock_value = self
        
#         # Add type-specific attributes
#         self.dtype = self
#         self.itemsize = size_bytes
#         self.alignment = size_bytes
    
#     def __int__(self):
#         return self.size_bytes
    
#     def __float__(self):
#         return float(self.size_bytes)

# # Safe constexpr that never fails
# def ultra_safe_constexpr(value):
#     """Ultra-safe constexpr that handles any value type"""
    
#     class UltraSafeConstExpr(RobustMockTritonType):
#         def __init__(self, val):
#             super().__init__("constexpr")
#             self.val = val
#             self.value = val
#             self._mock_value = val
        
#         def __call__(self, *args, **kwargs):
#             return self.val
        
#         def __int__(self):
#             try:
#                 return int(self.val)
#             except:
#                 return 0
        
#         def __float__(self):
#             try:
#                 return float(self.val)
#             except:
#                 return 0.0
        
#         def __str__(self):
#             return str(self.val)
    
#     return UltraSafeConstExpr(value)

# # Mock module creation with proper structure
# def create_robust_mock_module(name, parent_name=None):
#     """Create robust mock module"""
#     module = ModuleType(name)
    
#     spec = ModuleSpec(name, None)
#     spec.origin = "mock"
#     spec.submodule_search_locations = [] if parent_name else [f"mock_{name}"]
#     module.__spec__ = spec
#     module.__name__ = name
#     module.__file__ = "<mock>"
#     module.__package__ = parent_name if parent_name else name.split('.')[0]
#     module.__path__ = [f"mock_{name}"] if not parent_name else []
    
#     return module

# # Mock functions with robust error handling
# def robust_mock_jit(*args, **kwargs):
#     def decorator(func):
#         return func
#     return decorator

# def robust_mock_autotune(*args, **kwargs):
#     def decorator(func):
#         return func
#     return decorator

# def robust_mock_config(**kwargs):
#     class RobustMockConfig:
#         def __init__(self, **kwargs):
#             for k, v in kwargs.items():
#                 setattr(self, k, v)
        
#         def __getattr__(self, name):
#             return RobustMockTritonType(f"config.{name}")
    
#     return RobustMockConfig(**kwargs)

# # Install comprehensive triton mock
# def install_robust_triton_mock():
#     """Install the most robust triton mock possible"""
    
#     # Main triton module
#     triton_module = create_robust_mock_module('triton')
#     triton_module.jit = robust_mock_jit
#     triton_module.cdiv = lambda a, b: (a + b - 1) // b
#     triton_module.next_power_of_2 = lambda x: 1 << (max(0, x - 1)).bit_length()
#     triton_module.Config = robust_mock_config
#     triton_module.autotune = robust_mock_autotune
#     triton_module.heuristics = RobustMockTritonType("heuristics")
#     triton_module.__version__ = "2.1.0"
    
#     # Language module
#     triton_language = create_robust_mock_module('triton.language', 'triton')
#     triton_language.constexpr = ultra_safe_constexpr
    
#     # All functions as robust mocks
#     functions = [
#         'program_id', 'num_programs', 'arange', 'load', 'store', 'atomic_add',
#         'atomic_cas', 'atomic_xchg', 'atomic_max', 'atomic_min', 'atomic_and',
#         'atomic_or', 'atomic_xor', 'dot', 'dot_scaled', 'trans', 'broadcast_to',
#         'sum', 'max', 'min', 'maximum', 'minimum', 'where', 'exp', 'exp2',
#         'log', 'log2', 'log10', 'sqrt', 'rsqrt', 'sin', 'cos', 'tan', 'asin',
#         'acos', 'atan', 'atan2', 'sinh', 'cosh', 'tanh', 'asinh', 'acosh',
#         'atanh', 'floor', 'ceil', 'round', 'trunc', 'fmod', 'remainder', 'abs',
#         'pow', 'clamp', 'multiple_of', 'max_constancy', 'max_contiguous',
#         'static_print', 'static_assert', 'static_range', 'device_print',
#         'device_assert', 'debug_barrier', 'zeros', 'zeros_like', 'full',
#         'full_like', 'reshape', 'view', 'permute', 'transpose', 'expand_dims',
#         'squeeze', 'ravel', 'range', 'reduce', 'slice', 'split', 'join', 'cat',
#         'gather', 'scatter', 'histogram', 'make_block_ptr', 'advance',
#         'inline_asm_elementwise', 'dtype', 'tensor', 'tuple', 'tuple_type',
#         'pointer_type', 'pi32_t', 'semantic'
#     ]
    
#     for func_name in functions:
#         setattr(triton_language, func_name, RobustMockTritonType(func_name))
    
#     # Data types with guaranteed .value access
#     data_types = [
#         ('int1', 1), ('int8', 1), ('int16', 2), ('int32', 4), ('int64', 8),
#         ('uint8', 1), ('uint16', 2), ('uint32', 4), ('uint64', 8),
#         ('float16', 2), ('float32', 4), ('float64', 8), ('bfloat16', 2),
#         ('float8e4b15', 1), ('float8e4nv', 1), ('float8e4b8', 1),
#         ('float8e5', 1), ('float8e5b16', 1), ('float8e4m3fn', 1), ('float8e5m2', 1)
#     ]
    
#     for dtype_name, size in data_types:
#         setattr(triton_language, dtype_name, EnhancedMockDataType(dtype_name, size))
    
#     # Math module
#     triton_language_math = create_robust_mock_module('triton.language.math', 'triton.language')
#     math_functions = [
#         'abs', 'acos', 'acosh', 'asin', 'asinh', 'atan', 'atan2', 'atanh',
#         'ceil', 'clamp', 'cos', 'cosh', 'erf', 'erfc', 'exp', 'exp2', 'expm1',
#         'fabs', 'floor', 'fmod', 'frexp', 'gamma', 'isfinite', 'isinf', 'isnan',
#         'j0', 'j1', 'ldexp', 'lgamma', 'log', 'log10', 'log1p', 'log2', 'logb',
#         'modf', 'nearbyint', 'nextafter', 'pow', 'remainder', 'rint', 'round',
#         'rsqrt', 'scalb', 'sin', 'sinh', 'sqrt', 'tan', 'tanh', 'tgamma',
#         'trunc', 'y0', 'y1'
#     ]
    
#     for func_name in math_functions:
#         setattr(triton_language_math, func_name, RobustMockTritonType(f"math.{func_name}"))
    
#     triton_language.math = triton_language_math
    
#     # Other modules
#     other_modules = [
#         ('triton.ops', ['matmul', 'addmm', 'conv', 'flash_attention']),
#         ('triton.runtime', []),
#         ('triton.runtime.autotuner', ['Autotuner', 'Config', 'Heuristics']),
#         ('triton.runtime.jit', ['JITFunction', 'KernelInterface', 'MockTensor', 'TensorWrapper', 'reinterpret']),
#         ('triton.runtime.cache', ['get_cache_manager', 'get_dump_manager']),
#         ('triton.runtime.errors', ['OutOfResources', 'InterpreterError']),
#         ('triton.testing', ['perf_report', 'do_bench', 'assert_close']),
#         ('triton.compiler', ['compile', 'CompiledKernel']),
#         ('triton.heuristics', ['matmul', 'addmm']),
#         ('triton.profiler', ['profile', 'Profiler']),
#     ]
    
#     created_modules = {
#         'triton': triton_module,
#         'triton.language': triton_language,
#         'triton.language.math': triton_language_math,
#     }
    
#     for module_name, attrs in other_modules:
#         parts = module_name.split('.')
#         parent_name = '.'.join(parts[:-1]) if len(parts) > 1 else None
        
#         module = create_robust_mock_module(module_name, parent_name)
#         for attr_name in attrs:
#             setattr(module, attr_name, RobustMockTritonType(f"{module_name}.{attr_name}"))
        
#         created_modules[module_name] = module
    
#     # Install all modules
#     for module_name, module in created_modules.items():
#         sys.modules[module_name] = module
    
#     # Special handling for runtime hierarchy
#     sys.modules['triton.runtime.driver'] = create_robust_mock_module('triton.runtime.driver', 'triton.runtime')
#     sys.modules['triton.runtime.driver.active'] = create_robust_mock_module('triton.runtime.driver.active', 'triton.runtime.driver')
    
#     # Ensure language is a package
#     triton_language.__path__ = ['mock_triton_language']
    
#     print("[Robust Mock] Ultra-robust triton mock installed - should handle all .value access")
#     print("[Robust Mock] - All data types with guaranteed .value attribute")
#     print("[Robust Mock] - Comprehensive error handling for all operations")
#     print("[Robust Mock] - No built-in type patching required")

# # Install the robust mock
# install_robust_triton_mock()