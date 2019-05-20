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
    static bool development = {DEVELOPMENT};
    static bool profiler = {PROFILER};

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
        EditorUserBuildSettings.androidBuildSystem = AndroidBuildSystem.Gradle;

        SetScriptingBackend();
        SetVersions();


        string path = Path.Combine(outputProjectsFolder, 
                                   string.Format("{0}_{1}.apk", PlayerSettings.applicationIdentifier, PlayerSettings.bundleVersion));
        Build(path, BuildTarget.Android);
    }

    static void BuildWin()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                                   string.Format("{0}.exe", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneWindows);
    }
    static void BuildWin64()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                                    string.Format("{0}.exe", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneWindows64);
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
        Build(path, BuildTarget.StandaloneOSXUniversal);
#endif
    }

    static void BuildLinux()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                            string.Format("{0}", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneLinux);
    }

    static void BuildLinux64()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                            string.Format("{0}", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneLinux64);
    }

    static void BuildLinuxUniversal()
    {
        SetScriptingBackend();
        SetVersions();
        string path = Path.Combine(outputProjectsFolder, 
                            string.Format("{0}", PlayerSettings.productName));
        Build(path, BuildTarget.StandaloneLinuxUniversal);
    }

    static void BuildiOS()
    {
        EditorUserBuildSettings.iOSBuildConfigType = iOSBuildType.Release;
        if (development)
            EditorUserBuildSettings.iOSBuildConfigType = iOSBuildType.Debug;
        SetScriptingBackend();
        SetVersions();
        Build(outputProjectsFolder, BuildTarget.iOS);
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

    static void Build(string path, BuildTarget target)
    {
        BuildOptions options = BuildOptions.None;
        if (development)
            options |= BuildOptions.AllowDebugging | BuildOptions.Development;
        if (profiler)
            options |= BuildOptions.ConnectWithProfiler;
        string error = BuildPipeline.BuildPlayer(GetScenes(), path, target, options);

        if (string.IsNullOrEmpty(error))
            EditorApplication.Exit(0);
        else
            EditorApplication.Exit(1);
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