#if UNITY_EDITOR
using System;
using System.IO;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

public class BatchBuild
{
    static string outputProjectsFolder = "{BUILD_PATH}";
    static string scriptingBackend = "{SBACKEND}";
    static int overrideBuildNumber = {BUILD_NUMBER};
    static string overrideVersion = "{VERSION}";
    static string keystoreName = "{KEYSTORE}";
    static string keystorePass = "{KEYSTORE_PWD}";
    static string keyaliasName = "{KEY}";
    static string keyaliasPass = "{KEY_PWD}";
    static bool useAPKExpansionFiles = {SPLIT};
    static bool splitByArchitecture = {SPLIT_ARCH};
    static bool development = {DEVELOPMENT};
    static bool profiler = {PROFILER};
    static string buildWithMethod = "{BUILD_WITH_METHOD}";

    static void BuildAndroid()
    {
        PlayerSettings.Android.keystoreName = null;
        PlayerSettings.Android.keystorePass = null;
        PlayerSettings.Android.keyaliasName = null;
        PlayerSettings.Android.keyaliasPass = null;

        if (keystoreName.Length > 0)
        {
            PlayerSettings.Android.keystoreName = keystoreName;
            PlayerSettings.Android.keystorePass = keystorePass;
            PlayerSettings.Android.keyaliasName = keyaliasName;
            PlayerSettings.Android.keyaliasPass = keyaliasPass;
        }

        PlayerSettings.Android.useAPKExpansionFiles = useAPKExpansionFiles;
#if UNITY_2018_2_OR_NEWER
        PlayerSettings.Android.buildApkPerCpuArchitecture = splitByArchitecture;
#endif
        EditorUserBuildSettings.androidBuildSystem = AndroidBuildSystem.Gradle;

        SetScriptingBackend();
        SetVersions();


        string path = Path.Combine(outputProjectsFolder, 
                                   string.Format("{0}_{1}.apk", PlayerSettings.applicationIdentifier, PlayerSettings.bundleVersion));
        Build(path, BuildTarget.Android, GetOptions(), GetScenes());
    }

    static void BuildWin()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                                   string.Format("{0}.exe", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneWindows, GetOptions(), GetScenes());
    }
    static void BuildWin64()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                                    string.Format("{0}.exe", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneWindows64, GetOptions(), GetScenes());
    }

    static void BuildOSXUniversal()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                            string.Format("{0}.app", PlayerSettings.productName));
#if UNITY_2017_3_OR_NEWER
        Build(path, BuildTarget.StandaloneOSX);
#else
        Build(path, BuildTarget.StandaloneOSXUniversal, GetOptions(), GetScenes());
#endif
    }

    static void BuildLinux()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                            string.Format("{0}", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneLinux, GetOptions(), GetScenes());
    }

    static void BuildLinux64()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                            string.Format("{0}", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneLinux64, GetOptions(), GetScenes());
    }

    static void BuildLinuxUniversal()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                            string.Format("{0}", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneLinuxUniversal, GetOptions(), GetScenes());
    }

    static void BuildiOS()
    {
        EditorUserBuildSettings.iOSBuildConfigType = iOSBuildType.Release;
        if (development)
            EditorUserBuildSettings.iOSBuildConfigType = iOSBuildType.Debug;
        SetScriptingBackend();
        SetVersions();
        Build(outputProjectsFolder, BuildTarget.iOS, GetOptions(), GetScenes());
    }


    static BuildOptions GetOptions()
    {
        BuildOptions options = BuildOptions.None;
        if (development)
            options |= BuildOptions.AllowDebugging | BuildOptions.Development;
        if (profiler)
            options |= BuildOptions.ConnectWithProfiler;

        return options;
    }

    static void SetScriptingBackend()
    {
        if (scriptingBackend.ToLower() == "il2cpp")
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Android, ScriptingImplementation.IL2CPP);
        if (scriptingBackend.ToLower() == "mono")
            PlayerSettings.SetScriptingBackend(BuildTargetGroup.Android, ScriptingImplementation.Mono2x);
    }

    static void SetVersions()
    {
        if (overrideBuildNumber >= 0)
        {
            PlayerSettings.Android.bundleVersionCode = overrideBuildNumber;
            PlayerSettings.iOS.buildNumber = overrideBuildNumber.ToString();
        }

        if (!string.IsNullOrEmpty(overrideVersion))
            PlayerSettings.bundleVersion = overrideVersion;
    }

    static void Build(string path, BuildTarget target, BuildOptions options, string[] scenes)
    {
        if (!string.IsNullOrEmpty(buildWithMethod))
        {
            string[] splitted = buildWithMethod.Split('.');
            if (splitted.Length < 2)
                throw new System.ArgumentException("Build with method should be in format Namespace.Class.Method");
            string cls = string.Join(".", splitted.Take(splitted.Length - 1));
            string method = splitted[splitted.Length - 1];
            Type type = Type.GetType(cls, false, false);
            if (type == null)
                throw new System.ArgumentException($"Build with method class {cls} not found");

            MethodInfo methodInfo = type.GetMethod(method,
                BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            if (methodInfo == null)
                throw new System.ArgumentException($"Build with method {method} not found in class {cls}. It should be static");
            
            
            if ((bool)methodInfo.Invoke(null, path, target, options, scenes))
                EditorApplication.Exit(0);
            else
                EditorApplication.Exit(1);

            return;
        }

#if UNITY_2018_1_OR_NEWER
        UnityEditor.Build.Reporting.BuildReport report = BuildPipeline.BuildPlayer(scenes, path, target, options);

        if (report.summary.result == UnityEditor.Build.Reporting.BuildResult.Succeeded)
            EditorApplication.Exit(0);
        else
            EditorApplication.Exit(1);
#else
        string error = BuildPipeline.BuildPlayer(scenes, path, target, options);

        if (string.IsNullOrEmpty(error))
            EditorApplication.Exit(0);
        else
            EditorApplication.Exit(1);
#endif
    }

    static string[] GetScenes()
    {
        var projectScenes = EditorBuildSettings.scenes;
        List<string> scenesToBuild = new List<string>();
        for (int i = 0; i < projectScenes.Length; i++)
        {
            if (projectScenes[i].enabled)
            {
                scenesToBuild.Add(projectScenes[i].path);
            }
        }
        return scenesToBuild.ToArray();
    }
}
#endif