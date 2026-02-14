@REM ----------------------------------------------------------------------------
@REM  Copyright 2001-2006 The Apache Software Foundation.
@REM
@REM  Licensed under the Apache License, Version 2.0 (the "License");
@REM  you may not use this file except in compliance with the License.
@REM  You may obtain a copy of the License at
@REM
@REM       http://www.apache.org/licenses/LICENSE-2.0
@REM
@REM  Unless required by applicable law or agreed to in writing, software
@REM  distributed under the License is distributed on an "AS IS" BASIS,
@REM  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
@REM  See the License for the specific language governing permissions and
@REM  limitations under the License.
@REM ----------------------------------------------------------------------------
@REM
@REM   Copyright (c) 2001-2006 The Apache Software Foundation.  All rights
@REM   reserved.

@echo off

set ERROR_CODE=0

:init
@REM Decide how to startup depending on the version of windows

@REM -- Win98ME
if NOT "%OS%"=="Windows_NT" goto Win9xArg

@REM set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" @setlocal

@REM -- 4NT shell
if "%eval[2+2]" == "4" goto 4NTArgs

@REM -- Regular WinNT shell
set CMD_LINE_ARGS=%*
goto WinNTGetScriptDir

@REM The 4NT Shell from jp software
:4NTArgs
set CMD_LINE_ARGS=%$
goto WinNTGetScriptDir

:Win9xArg
@REM Slurp the command line arguments.  This loop allows for an unlimited number
@REM of arguments (up to the command line limit, anyway).
set CMD_LINE_ARGS=
:Win9xApp
if %1a==a goto Win9xGetScriptDir
set CMD_LINE_ARGS=%CMD_LINE_ARGS% %1
shift
goto Win9xApp

:Win9xGetScriptDir
set SAVEDIR=%CD%
%0\
cd %0\..\.. 
set BASEDIR=%CD%
cd %SAVEDIR%
set SAVE_DIR=
goto repoSetup

:WinNTGetScriptDir
set BASEDIR=%~dp0\..

:repoSetup
set REPO=


if "%JAVACMD%"=="" set JAVACMD=java

if "%REPO%"=="" set REPO=%BASEDIR%\repo

set CLASSPATH="%BASEDIR%"\etc;"%REPO%"\org\eclipse\elk\org.eclipse.elk.graph.json\0.11.0\org.eclipse.elk.graph.json-0.11.0.jar;"%REPO%"\com\google\guava\guava\33.5.0-jre\guava-33.5.0-jre.jar;"%REPO%"\com\google\guava\failureaccess\1.0.3\failureaccess-1.0.3.jar;"%REPO%"\com\google\guava\listenablefuture\9999.0-empty-to-avoid-conflict-with-guava\listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar;"%REPO%"\org\jspecify\jspecify\1.0.0\jspecify-1.0.0.jar;"%REPO%"\com\google\errorprone\error_prone_annotations\2.41.0\error_prone_annotations-2.41.0.jar;"%REPO%"\com\google\j2objc\j2objc-annotations\3.1\j2objc-annotations-3.1.jar;"%REPO%"\com\google\code\gson\gson\2.13.2\gson-2.13.2.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.core\0.11.0\org.eclipse.elk.core-0.11.0.jar;"%REPO%"\org\eclipse\emf\org.eclipse.emf.ecore.xmi\2.12.0\org.eclipse.emf.ecore.xmi-2.12.0.jar;"%REPO%"\org\eclipse\xtext\org.eclipse.xtext.xbase.lib\2.36.0\org.eclipse.xtext.xbase.lib-2.36.0.jar;"%REPO%"\org\eclipse\xtend\org.eclipse.xtend.lib\2.36.0\org.eclipse.xtend.lib-2.36.0.jar;"%REPO%"\org\eclipse\xtend\org.eclipse.xtend.lib.macro\2.36.0\org.eclipse.xtend.lib.macro-2.36.0.jar;"%REPO%"\commons-cli\commons-cli\1.4\commons-cli-1.4.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.layered\0.11.0\org.eclipse.elk.alg.layered-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.common\0.11.0\org.eclipse.elk.alg.common-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.graph\0.11.0\org.eclipse.elk.graph-0.11.0.jar;"%REPO%"\org\eclipse\emf\org.eclipse.emf.common\2.12.0\org.eclipse.emf.common-2.12.0.jar;"%REPO%"\org\eclipse\emf\org.eclipse.emf.ecore\2.12.0\org.eclipse.emf.ecore-2.12.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.disco\0.11.0\org.eclipse.elk.alg.disco-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.force\0.11.0\org.eclipse.elk.alg.force-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.graphviz.dot\0.11.0\org.eclipse.elk.alg.graphviz.dot-0.11.0.jar;"%REPO%"\org\eclipse\xtext\org.eclipse.xtext\2.36.0\org.eclipse.xtext-2.36.0.jar;"%REPO%"\org\eclipse\xtext\org.eclipse.xtext.util\2.36.0\org.eclipse.xtext.util-2.36.0.jar;"%REPO%"\ch\qos\reload4j\reload4j\1.2.25\reload4j-1.2.25.jar;"%REPO%"\org\eclipse\platform\org.eclipse.equinox.common\3.17.100\org.eclipse.equinox.common-3.17.100.jar;"%REPO%"\org\eclipse\platform\org.eclipse.osgi\3.18.300\org.eclipse.osgi-3.18.300.jar;"%REPO%"\com\google\inject\guice\7.0.0\guice-7.0.0.jar;"%REPO%"\jakarta\inject\jakarta.inject-api\2.0.1\jakarta.inject-api-2.0.1.jar;"%REPO%"\aopalliance\aopalliance\1.0\aopalliance-1.0.jar;"%REPO%"\org\antlr\antlr-runtime\3.2\antlr-runtime-3.2.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.graphviz.layouter\0.11.0\org.eclipse.elk.alg.graphviz.layouter-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.libavoid\0.11.0\org.eclipse.elk.alg.libavoid-0.11.0.jar;"%REPO%"\org\eclipse\platform\org.eclipse.core.runtime\3.31.0\org.eclipse.core.runtime-3.31.0.jar;"%REPO%"\org\eclipse\platform\org.eclipse.core.jobs\3.15.200\org.eclipse.core.jobs-3.15.200.jar;"%REPO%"\org\eclipse\platform\org.eclipse.equinox.registry\3.12.0\org.eclipse.equinox.registry-3.12.0.jar;"%REPO%"\org\eclipse\platform\org.eclipse.equinox.preferences\3.11.0\org.eclipse.equinox.preferences-3.11.0.jar;"%REPO%"\org\osgi\org.osgi.service.prefs\1.1.2\org.osgi.service.prefs-1.1.2.jar;"%REPO%"\org\osgi\osgi.annotation\8.0.1\osgi.annotation-8.0.1.jar;"%REPO%"\org\eclipse\platform\org.eclipse.core.contenttype\3.9.300\org.eclipse.core.contenttype-3.9.300.jar;"%REPO%"\org\eclipse\platform\org.eclipse.equinox.app\1.7.0\org.eclipse.equinox.app-1.7.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.mrtree\0.11.0\org.eclipse.elk.alg.mrtree-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.radial\0.11.0\org.eclipse.elk.alg.radial-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.rectpacking\0.11.0\org.eclipse.elk.alg.rectpacking-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.spore\0.11.0\org.eclipse.elk.alg.spore-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.topdownpacking\0.11.0\org.eclipse.elk.alg.topdownpacking-0.11.0.jar;"%REPO%"\org\eclipse\elk\org.eclipse.elk.alg.vertiflex\0.11.0\org.eclipse.elk.alg.vertiflex-0.11.0.jar;"%REPO%"\com\craigjb\elkjson\0.1\elkjson-0.1.jar

set ENDORSED_DIR=
if NOT "%ENDORSED_DIR%" == "" set CLASSPATH="%BASEDIR%"\%ENDORSED_DIR%\*;%CLASSPATH%

if NOT "%CLASSPATH_PREFIX%" == "" set CLASSPATH=%CLASSPATH_PREFIX%;%CLASSPATH%

@REM Reaching here means variables are defined and arguments have been captured
:endInit

%JAVACMD% %JAVA_OPTS%  -classpath %CLASSPATH% -Dapp.name="elkjson" -Dapp.repo="%REPO%" -Dapp.home="%BASEDIR%" -Dbasedir="%BASEDIR%" com.craigjb.elkjson.App %CMD_LINE_ARGS%
if %ERRORLEVEL% NEQ 0 goto error
goto end

:error
if "%OS%"=="Windows_NT" @endlocal
set ERROR_CODE=%ERRORLEVEL%

:end
@REM set local scope for the variables with windows NT shell
if "%OS%"=="Windows_NT" goto endNT

@REM For old DOS remove the set variables from ENV - we assume they were not set
@REM before we started - at least we don't leave any baggage around
set CMD_LINE_ARGS=
goto postExec

:endNT
@REM If error code is set to 1 then the endlocal was done already in :error.
if %ERROR_CODE% EQU 0 @endlocal


:postExec

if "%FORCE_EXIT_ON_ERROR%" == "on" (
  if %ERROR_CODE% NEQ 0 exit %ERROR_CODE%
)

exit /B %ERROR_CODE%
