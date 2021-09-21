
/* Return the compiler identification, if possible. */

#include "Python.h"

#ifndef COMPILER

// Note the __clang__ conditional has to come before the __GNUC__ one because
// clang pretends to be GCC.
#if defined(__clang__) && !defined(_WIN32)
#define COMPILER "[Clang " __clang_version__ "]"
#elif defined(__GNUC__)
/* To not break compatibility with things that determine
   CPU arch by calling get_build_version in msvccompiler.py
   (such as NumPy) add "32 bit" or "64 bit (AMD64)" on Windows
   and also use a space as a separator rather than a newline. */
#if defined(_WIN32)
#define COMP_SEP " "
#if defined(__x86_64__)
#define ARCH_SUFFIX " 64 bit (AMD64)"
#elif defined(__aarch64__)
#define ARCH_SUFFIX " 64 bit (ARM64)"
#else
#define ARCH_SUFFIX " 32 bit"
#endif
#else
#define COMP_SEP "\n"
#define ARCH_SUFFIX ""
#endif
#if defined(__clang__)
#define str(x) #x
#define xstr(x) str(x)
#define COMPILER COMP_SEP "[GCC Clang " xstr(__clang_major__) "." \
        xstr(__clang_minor__) "." xstr(__clang_patchlevel__) ARCH_SUFFIX "]"
#else
#if defined(_UCRT)
#define COMPILER COMP_SEP "[GCC UCRT " __VERSION__ ARCH_SUFFIX "]"
#else
#define COMPILER COMP_SEP "[GCC " __VERSION__ ARCH_SUFFIX "]"
#endif
#endif
// Generic fallbacks.
#elif defined(__cplusplus)
#define COMPILER "[C++]"
#else
#define COMPILER "[C]"
#endif

#endif /* !COMPILER */

const char *
Py_GetCompiler(void)
{
    return COMPILER;
}
