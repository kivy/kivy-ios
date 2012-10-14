/*
  Simple DirectMedia Layer
  Copyright (C) 1997-2012 Sam Lantinga <slouken@libsdl.org>

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the authors be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.
*/
#include "SDL_config.h"
#include "SDL_stdinc.h"
#include "SDL_assert.h"

#ifdef __ANDROID__

#include "SDL_android.h"

extern "C" {
#include "../../events/SDL_events_c.h"
#include "../../video/android/SDL_androidkeyboard.h"
#include "../../video/android/SDL_androidtouch.h"
#include "../../video/android/SDL_androidvideo.h"

#include <android/log.h>
#include <pthread.h>
#define LOG_TAG "SDL_android"
//#define LOGI(...)  __android_log_print(ANDROID_LOG_INFO,LOG_TAG,__VA_ARGS__)
//#define LOGE(...)  __android_log_print(ANDROID_LOG_ERROR,LOG_TAG,__VA_ARGS__)
#define LOGI(...) do {} while (false)
#define LOGE(...) do {} while (false)


/* Implemented in audio/android/SDL_androidaudio.c */
extern void Android_RunAudioThread();
} // C

/*******************************************************************************
 This file links the Java side of Android with libsdl
*******************************************************************************/
#include <jni.h>
#include <android/log.h>


/*******************************************************************************
                               Globals
*******************************************************************************/
static pthread_key_t mThreadKey;
static JavaVM* mJavaVM;

// Main activity
static jclass mActivityClass;

// method signatures
static jmethodID midCreateGLContext;
static jmethodID midFlipBuffers;
static jmethodID midAudioInit;
static jmethodID midAudioWriteShortBuffer;
static jmethodID midAudioWriteByteBuffer;
static jmethodID midAudioQuit;

// Accelerometer data storage
static float fLastAccelerometer[3];
static bool bHasNewData;

/*******************************************************************************
                 Functions called by JNI
*******************************************************************************/

// Library init
extern "C" jint JNI_OnLoad(JavaVM* vm, void* reserved)
{
    JNIEnv *env;
    mJavaVM = vm;
    LOGI("JNI_OnLoad called");
    if (mJavaVM->GetEnv((void**) &env, JNI_VERSION_1_4) != JNI_OK) {
        LOGE("Failed to get the environment using GetEnv()");
        return -1;
    }
    /*
     * Create mThreadKey so we can keep track of the JNIEnv assigned to each thread
     * Refer to http://developer.android.com/guide/practices/design/jni.html for the rationale behind this
     */
    if (pthread_key_create(&mThreadKey, Android_JNI_ThreadDestroyed)) {
        __android_log_print(ANDROID_LOG_ERROR, "SDL", "Error initializing pthread key");
    }
    else {
        Android_JNI_SetupThread();
    }

    return JNI_VERSION_1_4;
}

// Called before SDL_main() to initialize JNI bindings
extern "C" void SDL_Android_Init(JNIEnv* mEnv, jclass cls)
{
    __android_log_print(ANDROID_LOG_INFO, "SDL", "SDL_Android_Init()");

    Android_JNI_SetupThread();

    mActivityClass = (jclass)mEnv->NewGlobalRef(cls);

    midCreateGLContext = mEnv->GetStaticMethodID(mActivityClass,
                                "createGLContext","(II)Z");
    midFlipBuffers = mEnv->GetStaticMethodID(mActivityClass,
                                "flipBuffers","()V");
    midAudioInit = mEnv->GetStaticMethodID(mActivityClass, 
                                "audioInit", "(IZZI)Ljava/lang/Object;");
    midAudioWriteShortBuffer = mEnv->GetStaticMethodID(mActivityClass,
                                "audioWriteShortBuffer", "([S)V");
    midAudioWriteByteBuffer = mEnv->GetStaticMethodID(mActivityClass,
                                "audioWriteByteBuffer", "([B)V");
    midAudioQuit = mEnv->GetStaticMethodID(mActivityClass,
                                "audioQuit", "()V");

    bHasNewData = false;

    if(!midCreateGLContext || !midFlipBuffers || !midAudioInit ||
       !midAudioWriteShortBuffer || !midAudioWriteByteBuffer || !midAudioQuit) {
        __android_log_print(ANDROID_LOG_WARN, "SDL", "SDL: Couldn't locate Java callbacks, check that they're named and typed correctly");
    }
    __android_log_print(ANDROID_LOG_INFO, "SDL", "SDL_Android_Init() finished!");
}

// Resize
extern "C" void Java_org_libsdl_app_SDLActivity_onNativeResize(
                                    JNIEnv* env, jclass jcls,
                                    jint width, jint height, jint format)
{
    Android_SetScreenResolution(width, height, format);
}

// Keydown
extern "C" void Java_org_libsdl_app_SDLActivity_onNativeKeyDown(
                                    JNIEnv* env, jclass jcls, jint keycode)
{
    Android_OnKeyDown(keycode);
}

// Keyup
extern "C" void Java_org_libsdl_app_SDLActivity_onNativeKeyUp(
                                    JNIEnv* env, jclass jcls, jint keycode)
{
    Android_OnKeyUp(keycode);
}

// Touch
extern "C" void Java_org_libsdl_app_SDLActivity_onNativeTouch(
                                    JNIEnv* env, jclass jcls,
                                    jint touch_device_id_in, jint pointer_finger_id_in,
                                    jint action, jfloat x, jfloat y, jfloat p)
{
    Android_OnTouch(touch_device_id_in, pointer_finger_id_in, action, x, y, p);
}

// Accelerometer
extern "C" void Java_org_libsdl_app_SDLActivity_onNativeAccel(
                                    JNIEnv* env, jclass jcls,
                                    jfloat x, jfloat y, jfloat z)
{
    fLastAccelerometer[0] = x;
    fLastAccelerometer[1] = y;
    fLastAccelerometer[2] = z;
    bHasNewData = true;
}

// Quit
extern "C" void Java_org_libsdl_app_SDLActivity_nativeQuit(
                                    JNIEnv* env, jclass cls)
{    
    // Inject a SDL_QUIT event
    SDL_SendQuit();
}

// Pause
extern "C" void Java_org_libsdl_app_SDLActivity_nativePause(
                                    JNIEnv* env, jclass cls)
{
    if (Android_Window) {
        /* Signal the pause semaphore so the event loop knows to pause and (optionally) block itself */
        if (!SDL_SemValue(Android_PauseSem)) SDL_SemPost(Android_PauseSem);
        SDL_SendWindowEvent(Android_Window, SDL_WINDOWEVENT_FOCUS_LOST, 0, 0);
        SDL_SendWindowEvent(Android_Window, SDL_WINDOWEVENT_MINIMIZED, 0, 0);
    }
}

// Resume
extern "C" void Java_org_libsdl_app_SDLActivity_nativeResume(
                                    JNIEnv* env, jclass cls)
{
    if (Android_Window) {
        /* Signal the resume semaphore so the event loop knows to resume and restore the GL Context
         * We can't restore the GL Context here because it needs to be done on the SDL main thread
         * and this function will be called from the Java thread instead.
         */
        if (!SDL_SemValue(Android_ResumeSem)) SDL_SemPost(Android_ResumeSem);
        SDL_SendWindowEvent(Android_Window, SDL_WINDOWEVENT_FOCUS_GAINED, 0, 0);
        SDL_SendWindowEvent(Android_Window, SDL_WINDOWEVENT_RESTORED, 0, 0);
    }
}

extern "C" void Java_org_libsdl_app_SDLActivity_nativeRunAudioThread(
                                    JNIEnv* env, jclass cls)
{
    /* This is the audio thread, with a different environment */
    Android_JNI_SetupThread();

    Android_RunAudioThread();
}

extern "C" void Java_org_libsdl_app_SDLInputConnection_nativeCommitText(
                                    JNIEnv* env, jclass cls,
                                    jstring text, jint newCursorPosition)
{
    const char *utftext = env->GetStringUTFChars(text, NULL);

    SDL_SendKeyboardText(utftext);

    env->ReleaseStringUTFChars(text, utftext);
}

extern "C" void Java_org_libsdl_app_SDLInputConnection_nativeSetComposingText(
                                    JNIEnv* env, jclass cls,
                                    jstring text, jint newCursorPosition)
{
    const char *utftext = env->GetStringUTFChars(text, NULL);

    SDL_SendEditingText(utftext, 0, 0);

    env->ReleaseStringUTFChars(text, utftext);
}




/*******************************************************************************
             Functions called by SDL into Java
*******************************************************************************/

class LocalReferenceHolder
{
private:
    static int s_active;

public:
    static bool IsActive() {
        return s_active > 0;
    }

public:
    LocalReferenceHolder() : m_env(NULL) { }
    ~LocalReferenceHolder() {
        if (m_env) {
            m_env->PopLocalFrame(NULL);
            --s_active;
        }
    }

    bool init(JNIEnv *env, jint capacity = 16) {
        if (env->PushLocalFrame(capacity) < 0) {
            SDL_SetError("Failed to allocate enough JVM local references");
            return false;
        }
        ++s_active;
        m_env = env;
        return true;
    }

protected:
    JNIEnv *m_env;
};
int LocalReferenceHolder::s_active;

extern "C" SDL_bool Android_JNI_CreateContext(int majorVersion, int minorVersion)
{
    JNIEnv *mEnv = Android_JNI_GetEnv();
    if (mEnv->CallStaticBooleanMethod(mActivityClass, midCreateGLContext, majorVersion, minorVersion)) {
        return SDL_TRUE;
    } else {
        return SDL_FALSE;
    }
}

extern "C" void Android_JNI_SwapWindow()
{
    JNIEnv *mEnv = Android_JNI_GetEnv();
    mEnv->CallStaticVoidMethod(mActivityClass, midFlipBuffers); 
}

extern "C" void Android_JNI_SetActivityTitle(const char *title)
{
    jmethodID mid;
    JNIEnv *mEnv = Android_JNI_GetEnv();
    mid = mEnv->GetStaticMethodID(mActivityClass,"setActivityTitle","(Ljava/lang/String;)V");
    if (mid) {
        jstring jtitle = reinterpret_cast<jstring>(mEnv->NewStringUTF(title));
        mEnv->CallStaticVoidMethod(mActivityClass, mid, jtitle);
        mEnv->DeleteLocalRef(jtitle);
    }
}

extern "C" SDL_bool Android_JNI_GetAccelerometerValues(float values[3])
{
    int i;
    SDL_bool retval = SDL_FALSE;

    if (bHasNewData) {
        for (i = 0; i < 3; ++i) {
            values[i] = fLastAccelerometer[i];
        }
        bHasNewData = false;
        retval = SDL_TRUE;
    }

    return retval;
}

static void Android_JNI_ThreadDestroyed(void* value) {
    /* The thread is being destroyed, detach it from the Java VM and set the mThreadKey value to NULL as required */
    JNIEnv *env = (JNIEnv*) value;
    if (env != NULL) {
        mJavaVM->DetachCurrentThread();
        pthread_setspecific(mThreadKey, NULL);
    }
}

JNIEnv* Android_JNI_GetEnv(void) {
    /* From http://developer.android.com/guide/practices/jni.html
     * All threads are Linux threads, scheduled by the kernel.
     * They're usually started from managed code (using Thread.start), but they can also be created elsewhere and then
     * attached to the JavaVM. For example, a thread started with pthread_create can be attached with the
     * JNI AttachCurrentThread or AttachCurrentThreadAsDaemon functions. Until a thread is attached, it has no JNIEnv,
     * and cannot make JNI calls.
     * Attaching a natively-created thread causes a java.lang.Thread object to be constructed and added to the "main"
     * ThreadGroup, making it visible to the debugger. Calling AttachCurrentThread on an already-attached thread
     * is a no-op.
     * Note: You can call this function any number of times for the same thread, there's no harm in it
     */

    JNIEnv *env;
    int status = mJavaVM->AttachCurrentThread(&env, NULL);
    if(status < 0) {
        LOGE("failed to attach current thread");
        return 0;
    }

    return env;
}

int Android_JNI_SetupThread(void) {
    /* From http://developer.android.com/guide/practices/jni.html
     * Threads attached through JNI must call DetachCurrentThread before they exit. If coding this directly is awkward,
     * in Android 2.0 (Eclair) and higher you can use pthread_key_create to define a destructor function that will be
     * called before the thread exits, and call DetachCurrentThread from there. (Use that key with pthread_setspecific
     * to store the JNIEnv in thread-local-storage; that way it'll be passed into your destructor as the argument.)
     * Note: The destructor is not called unless the stored value is != NULL
     * Note: You can call this function any number of times for the same thread, there's no harm in it
     *       (except for some lost CPU cycles)
     */
    JNIEnv *env = Android_JNI_GetEnv();
    pthread_setspecific(mThreadKey, (void*) env);
    return 1;
}

//
// Audio support
//
static jboolean audioBuffer16Bit = JNI_FALSE;
static jboolean audioBufferStereo = JNI_FALSE;
static jobject audioBuffer = NULL;
static void* audioBufferPinned = NULL;

extern "C" int Android_JNI_OpenAudioDevice(int sampleRate, int is16Bit, int channelCount, int desiredBufferFrames)
{
    int audioBufferFrames;

    int status;
    JNIEnv *env = Android_JNI_GetEnv();

    if (!env) {
        LOGE("callback_handler: failed to attach current thread");
    }
    Android_JNI_SetupThread();

    
    __android_log_print(ANDROID_LOG_VERBOSE, "SDL", "SDL audio: opening device");
    audioBuffer16Bit = is16Bit;
    audioBufferStereo = channelCount > 1;

    audioBuffer = env->CallStaticObjectMethod(mActivityClass, midAudioInit, sampleRate, audioBuffer16Bit, audioBufferStereo, desiredBufferFrames);

    if (audioBuffer == NULL) {
        __android_log_print(ANDROID_LOG_WARN, "SDL", "SDL audio: didn't get back a good audio buffer!");
        return 0;
    }
    audioBuffer = env->NewGlobalRef(audioBuffer);

    jboolean isCopy = JNI_FALSE;
    if (audioBuffer16Bit) {
        audioBufferPinned = env->GetShortArrayElements((jshortArray)audioBuffer, &isCopy);
        audioBufferFrames = env->GetArrayLength((jshortArray)audioBuffer);
    } else {
        audioBufferPinned = env->GetByteArrayElements((jbyteArray)audioBuffer, &isCopy);
        audioBufferFrames = env->GetArrayLength((jbyteArray)audioBuffer);
    }
    if (audioBufferStereo) {
        audioBufferFrames /= 2;
    }
 
    return audioBufferFrames;
}

extern "C" void * Android_JNI_GetAudioBuffer()
{
    return audioBufferPinned;
}

extern "C" void Android_JNI_WriteAudioBuffer()
{
    JNIEnv *mAudioEnv = Android_JNI_GetEnv();

    if (audioBuffer16Bit) {
        mAudioEnv->ReleaseShortArrayElements((jshortArray)audioBuffer, (jshort *)audioBufferPinned, JNI_COMMIT);
        mAudioEnv->CallStaticVoidMethod(mActivityClass, midAudioWriteShortBuffer, (jshortArray)audioBuffer);
    } else {
        mAudioEnv->ReleaseByteArrayElements((jbyteArray)audioBuffer, (jbyte *)audioBufferPinned, JNI_COMMIT);
        mAudioEnv->CallStaticVoidMethod(mActivityClass, midAudioWriteByteBuffer, (jbyteArray)audioBuffer);
    }

    /* JNI_COMMIT means the changes are committed to the VM but the buffer remains pinned */
}

extern "C" void Android_JNI_CloseAudioDevice()
{
    int status;
    JNIEnv *env = Android_JNI_GetEnv();

    env->CallStaticVoidMethod(mActivityClass, midAudioQuit); 

    if (audioBuffer) {
        env->DeleteGlobalRef(audioBuffer);
        audioBuffer = NULL;
        audioBufferPinned = NULL;
    }
}

// Test for an exception and call SDL_SetError with its detail if one occurs
static bool Android_JNI_ExceptionOccurred()
{
    SDL_assert(LocalReferenceHolder::IsActive());
    JNIEnv *mEnv = Android_JNI_GetEnv();

    jthrowable exception = mEnv->ExceptionOccurred();
    if (exception != NULL) {
        jmethodID mid;

        // Until this happens most JNI operations have undefined behaviour
        mEnv->ExceptionClear();

        jclass exceptionClass = mEnv->GetObjectClass(exception);
        jclass classClass = mEnv->FindClass("java/lang/Class");

        mid = mEnv->GetMethodID(classClass, "getName", "()Ljava/lang/String;");
        jstring exceptionName = (jstring)mEnv->CallObjectMethod(exceptionClass, mid);
        const char* exceptionNameUTF8 = mEnv->GetStringUTFChars(exceptionName, 0);

        mid = mEnv->GetMethodID(exceptionClass, "getMessage", "()Ljava/lang/String;");
        jstring exceptionMessage = (jstring)mEnv->CallObjectMethod(exception, mid);

        if (exceptionMessage != NULL) {
            const char* exceptionMessageUTF8 = mEnv->GetStringUTFChars(
                    exceptionMessage, 0);
            SDL_SetError("%s: %s", exceptionNameUTF8, exceptionMessageUTF8);
            mEnv->ReleaseStringUTFChars(exceptionMessage, exceptionMessageUTF8);
        } else {
            SDL_SetError("%s", exceptionNameUTF8);
        }

        mEnv->ReleaseStringUTFChars(exceptionName, exceptionNameUTF8);

        return true;
    }

    return false;
}

static int Android_JNI_FileOpen(SDL_RWops* ctx)
{
    LocalReferenceHolder refs;
    int result = 0;

    jmethodID mid;
    jobject context;
    jobject assetManager;
    jobject inputStream;
    jclass channels;
    jobject readableByteChannel;
    jstring fileNameJString;

    JNIEnv *mEnv = Android_JNI_GetEnv();
    if (!refs.init(mEnv)) {
        goto failure;
    }

    fileNameJString = (jstring)ctx->hidden.androidio.fileNameRef;

    // context = SDLActivity.getContext();
    mid = mEnv->GetStaticMethodID(mActivityClass,
            "getContext","()Landroid/content/Context;");
    context = mEnv->CallStaticObjectMethod(mActivityClass, mid);

    // assetManager = context.getAssets();
    mid = mEnv->GetMethodID(mEnv->GetObjectClass(context),
            "getAssets", "()Landroid/content/res/AssetManager;");
    assetManager = mEnv->CallObjectMethod(context, mid);

    // inputStream = assetManager.open(<filename>);
    mid = mEnv->GetMethodID(mEnv->GetObjectClass(assetManager),
            "open", "(Ljava/lang/String;)Ljava/io/InputStream;");
    inputStream = mEnv->CallObjectMethod(assetManager, mid, fileNameJString);
    if (Android_JNI_ExceptionOccurred()) {
        goto failure;
    }

    ctx->hidden.androidio.inputStreamRef = mEnv->NewGlobalRef(inputStream);

    // Despite all the visible documentation on [Asset]InputStream claiming
    // that the .available() method is not guaranteed to return the entire file
    // size, comments in <sdk>/samples/<ver>/ApiDemos/src/com/example/ ...
    // android/apis/content/ReadAsset.java imply that Android's
    // AssetInputStream.available() /will/ always return the total file size

    // size = inputStream.available();
    mid = mEnv->GetMethodID(mEnv->GetObjectClass(inputStream),
            "available", "()I");
    ctx->hidden.androidio.size = mEnv->CallIntMethod(inputStream, mid);
    if (Android_JNI_ExceptionOccurred()) {
        goto failure;
    }

    // readableByteChannel = Channels.newChannel(inputStream);
    channels = mEnv->FindClass("java/nio/channels/Channels");
    mid = mEnv->GetStaticMethodID(channels,
            "newChannel",
            "(Ljava/io/InputStream;)Ljava/nio/channels/ReadableByteChannel;");
    readableByteChannel = mEnv->CallStaticObjectMethod(
            channels, mid, inputStream);
    if (Android_JNI_ExceptionOccurred()) {
        goto failure;
    }

    ctx->hidden.androidio.readableByteChannelRef =
        mEnv->NewGlobalRef(readableByteChannel);

    // Store .read id for reading purposes
    mid = mEnv->GetMethodID(mEnv->GetObjectClass(readableByteChannel),
            "read", "(Ljava/nio/ByteBuffer;)I");
    ctx->hidden.androidio.readMethod = mid;

    ctx->hidden.androidio.position = 0;

    if (false) {
failure:
        result = -1;

        mEnv->DeleteGlobalRef((jobject)ctx->hidden.androidio.fileNameRef);

        if(ctx->hidden.androidio.inputStreamRef != NULL) {
            mEnv->DeleteGlobalRef((jobject)ctx->hidden.androidio.inputStreamRef);
        }

        if(ctx->hidden.androidio.readableByteChannelRef != NULL) {
            mEnv->DeleteGlobalRef((jobject)ctx->hidden.androidio.readableByteChannelRef);
        }

    }

    return result;
}

extern "C" int Android_JNI_FileOpen(SDL_RWops* ctx,
        const char* fileName, const char*)
{
    LocalReferenceHolder refs;
    JNIEnv *mEnv = Android_JNI_GetEnv();

    if (!refs.init(mEnv)) {
        return -1;
    }

    if (!ctx) {
        return -1;
    }

    jstring fileNameJString = mEnv->NewStringUTF(fileName);
    ctx->hidden.androidio.fileNameRef = mEnv->NewGlobalRef(fileNameJString);
    ctx->hidden.androidio.inputStreamRef = NULL;
    ctx->hidden.androidio.readableByteChannelRef = NULL;
    ctx->hidden.androidio.readMethod = NULL;

    return Android_JNI_FileOpen(ctx);
}

extern "C" size_t Android_JNI_FileRead(SDL_RWops* ctx, void* buffer,
        size_t size, size_t maxnum)
{
    LocalReferenceHolder refs;
    jlong bytesRemaining = (jlong) (size * maxnum);
    jlong bytesMax = (jlong) (ctx->hidden.androidio.size -  ctx->hidden.androidio.position);
    int bytesRead = 0;

    /* Don't read more bytes than those that remain in the file, otherwise we get an exception */
    if (bytesRemaining >  bytesMax) bytesRemaining = bytesMax;

    JNIEnv *mEnv = Android_JNI_GetEnv();
    if (!refs.init(mEnv)) {
        return -1;
    }

    jobject readableByteChannel = (jobject)ctx->hidden.androidio.readableByteChannelRef;
    jmethodID readMethod = (jmethodID)ctx->hidden.androidio.readMethod;
    jobject byteBuffer = mEnv->NewDirectByteBuffer(buffer, bytesRemaining);

    while (bytesRemaining > 0) {
        // result = readableByteChannel.read(...);
        int result = mEnv->CallIntMethod(readableByteChannel, readMethod, byteBuffer);

        if (Android_JNI_ExceptionOccurred()) {
            return 0;
        }

        if (result < 0) {
            break;
        }

        bytesRemaining -= result;
        bytesRead += result;
        ctx->hidden.androidio.position += result;
    }

    return bytesRead / size;
}

extern "C" size_t Android_JNI_FileWrite(SDL_RWops* ctx, const void* buffer,
        size_t size, size_t num)
{
    SDL_SetError("Cannot write to Android package filesystem");
    return 0;
}

static int Android_JNI_FileClose(SDL_RWops* ctx, bool release)
{
    LocalReferenceHolder refs;
    int result = 0;
    JNIEnv *mEnv = Android_JNI_GetEnv();

    if (!refs.init(mEnv)) {
        SDL_SetError("Failed to allocate enough JVM local references");
        return -1;
    }

    if (ctx) {
        if (release) {
            mEnv->DeleteGlobalRef((jobject)ctx->hidden.androidio.fileNameRef);
        }

        jobject inputStream = (jobject)ctx->hidden.androidio.inputStreamRef;

        // inputStream.close();
        jmethodID mid = mEnv->GetMethodID(mEnv->GetObjectClass(inputStream),
                "close", "()V");
        mEnv->CallVoidMethod(inputStream, mid);
        mEnv->DeleteGlobalRef((jobject)ctx->hidden.androidio.inputStreamRef);
        mEnv->DeleteGlobalRef((jobject)ctx->hidden.androidio.readableByteChannelRef);
        if (Android_JNI_ExceptionOccurred()) {
            result = -1;
        }

        if (release) {
            SDL_FreeRW(ctx);
        }
    }

    return result;
}


extern "C" long Android_JNI_FileSeek(SDL_RWops* ctx, long offset, int whence)
{
    long newPosition;

    switch (whence) {
        case RW_SEEK_SET:
            newPosition = offset;
            break;
        case RW_SEEK_CUR:
            newPosition = ctx->hidden.androidio.position + offset;
            break;
        case RW_SEEK_END:
            newPosition = ctx->hidden.androidio.size + offset;
            break;
        default:
            SDL_SetError("Unknown value for 'whence'");
            return -1;
    }
    if (newPosition < 0) {
        newPosition = 0;
    }
    if (newPosition > ctx->hidden.androidio.size) {
        newPosition = ctx->hidden.androidio.size;
    }

    long movement = newPosition - ctx->hidden.androidio.position;
    jobject inputStream = (jobject)ctx->hidden.androidio.inputStreamRef;

    if (movement > 0) {
        unsigned char buffer[1024];

        // The easy case where we're seeking forwards
        while (movement > 0) {
            long amount = (long) sizeof (buffer);
            if (amount > movement) {
                amount = movement;
            }
            size_t result = Android_JNI_FileRead(ctx, buffer, 1, amount);

            if (result <= 0) {
                // Failed to read/skip the required amount, so fail
                return -1;
            }

            movement -= result;
        }
    } else if (movement < 0) {
        // We can't seek backwards so we have to reopen the file and seek
        // forwards which obviously isn't very efficient
        Android_JNI_FileClose(ctx, false);
        Android_JNI_FileOpen(ctx);
        Android_JNI_FileSeek(ctx, newPosition, RW_SEEK_SET);
    }

    ctx->hidden.androidio.position = newPosition;

    return ctx->hidden.androidio.position;
}

extern "C" int Android_JNI_FileClose(SDL_RWops* ctx)
{
    return Android_JNI_FileClose(ctx, true);
}

// returns a new global reference which needs to be released later
static jobject Android_JNI_GetSystemServiceObject(const char* name)
{
    LocalReferenceHolder refs;
    JNIEnv* env = Android_JNI_GetEnv();
    if (!refs.init(env)) {
        return NULL;
    }

    jstring service = env->NewStringUTF(name);

    jmethodID mid;

    mid = env->GetStaticMethodID(mActivityClass, "getContext", "()Landroid/content/Context;");
    jobject context = env->CallStaticObjectMethod(mActivityClass, mid);

    mid = env->GetMethodID(mActivityClass, "getSystemService", "(Ljava/lang/String;)Ljava/lang/Object;");
    jobject manager = env->CallObjectMethod(context, mid, service);

    env->DeleteLocalRef(service);

    return manager ? env->NewGlobalRef(manager) : NULL;
}

#define SETUP_CLIPBOARD(error) \
    LocalReferenceHolder refs; \
    JNIEnv* env = Android_JNI_GetEnv(); \
    if (!refs.init(env)) { \
        return error; \
    } \
    jobject clipboard = Android_JNI_GetSystemServiceObject("clipboard"); \
    if (!clipboard) { \
        return error; \
    }

extern "C" int Android_JNI_SetClipboardText(const char* text)
{
    SETUP_CLIPBOARD(-1)

    jmethodID mid = env->GetMethodID(env->GetObjectClass(clipboard), "setText", "(Ljava/lang/CharSequence;)V");
    jstring string = env->NewStringUTF(text);
    env->CallVoidMethod(clipboard, mid, string);
    env->DeleteGlobalRef(clipboard);
    env->DeleteLocalRef(string);
    return 0;
}

extern "C" char* Android_JNI_GetClipboardText()
{
    SETUP_CLIPBOARD(SDL_strdup(""))

    jmethodID mid = env->GetMethodID(env->GetObjectClass(clipboard), "getText", "()Ljava/lang/CharSequence;");
    jobject sequence = env->CallObjectMethod(clipboard, mid);
    env->DeleteGlobalRef(clipboard);
    if (sequence) {
        mid = env->GetMethodID(env->GetObjectClass(sequence), "toString", "()Ljava/lang/String;");
        jstring string = reinterpret_cast<jstring>(env->CallObjectMethod(sequence, mid));
        const char* utf = env->GetStringUTFChars(string, 0);
        if (utf) {
            char* text = SDL_strdup(utf);
            env->ReleaseStringUTFChars(string, utf);
            return text;
        }
    }
    return SDL_strdup("");
}

extern "C" SDL_bool Android_JNI_HasClipboardText()
{
    SETUP_CLIPBOARD(SDL_FALSE)

    jmethodID mid = env->GetMethodID(env->GetObjectClass(clipboard), "hasText", "()Z");
    jboolean has = env->CallBooleanMethod(clipboard, mid);
    env->DeleteGlobalRef(clipboard);
    return has ? SDL_TRUE : SDL_FALSE;
}


// returns 0 on success or -1 on error (others undefined then)
// returns truthy or falsy value in plugged, charged and battery
// returns the value in seconds and percent or -1 if not available
extern "C" int Android_JNI_GetPowerInfo(int* plugged, int* charged, int* battery, int* seconds, int* percent)
{
    LocalReferenceHolder refs;
    JNIEnv* env = Android_JNI_GetEnv();
    if (!refs.init(env)) {
        return -1;
    }

    jmethodID mid;

    mid = env->GetStaticMethodID(mActivityClass, "getContext", "()Landroid/content/Context;");
    jobject context = env->CallStaticObjectMethod(mActivityClass, mid);

    jstring action = env->NewStringUTF("android.intent.action.BATTERY_CHANGED");

    jclass cls = env->FindClass("android/content/IntentFilter");

    mid = env->GetMethodID(cls, "<init>", "(Ljava/lang/String;)V");
    jobject filter = env->NewObject(cls, mid, action);

    env->DeleteLocalRef(action);

    mid = env->GetMethodID(mActivityClass, "registerReceiver", "(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;)Landroid/content/Intent;");
    jobject intent = env->CallObjectMethod(context, mid, NULL, filter);

    env->DeleteLocalRef(filter);

    cls = env->GetObjectClass(intent);

    jstring iname;
    jmethodID imid = env->GetMethodID(cls, "getIntExtra", "(Ljava/lang/String;I)I");

#define GET_INT_EXTRA(var, key) \
    iname = env->NewStringUTF(key); \
    int var = env->CallIntMethod(intent, imid, iname, -1); \
    env->DeleteLocalRef(iname);

    jstring bname;
    jmethodID bmid = env->GetMethodID(cls, "getBooleanExtra", "(Ljava/lang/String;Z)Z");

#define GET_BOOL_EXTRA(var, key) \
    bname = env->NewStringUTF(key); \
    int var = env->CallBooleanMethod(intent, bmid, bname, JNI_FALSE); \
    env->DeleteLocalRef(bname);

    if (plugged) {
        GET_INT_EXTRA(plug, "plugged") // == BatteryManager.EXTRA_PLUGGED (API 5)
        if (plug == -1) {
            return -1;
        }
        // 1 == BatteryManager.BATTERY_PLUGGED_AC
        // 2 == BatteryManager.BATTERY_PLUGGED_USB
        *plugged = (0 < plug) ? 1 : 0;
    }

    if (charged) {
        GET_INT_EXTRA(status, "status") // == BatteryManager.EXTRA_STATUS (API 5)
        if (status == -1) {
            return -1;
        }
        // 5 == BatteryManager.BATTERY_STATUS_FULL
        *charged = (status == 5) ? 1 : 0;
    }

    if (battery) {
        GET_BOOL_EXTRA(present, "present") // == BatteryManager.EXTRA_PRESENT (API 5)
        *battery = present ? 1 : 0;
    }

    if (seconds) {
        *seconds = -1; // not possible
    }

    if (percent) {
        GET_INT_EXTRA(level, "level") // == BatteryManager.EXTRA_LEVEL (API 5)
        GET_INT_EXTRA(scale, "scale") // == BatteryManager.EXTRA_SCALE (API 5)
        if ((level == -1) || (scale == -1)) {
            return -1;
        }
        *percent = level * 100 / scale;
    }

    env->DeleteLocalRef(intent);

    return 0;
}

// sends message to be handled on the UI event dispatch thread
extern "C" int Android_JNI_SendMessage(int command, int param)
{
    JNIEnv *env = Android_JNI_GetEnv();
    if (!env) {
        return -1;
    }
    jmethodID mid = env->GetStaticMethodID(mActivityClass, "sendMessage", "(II)V");
    if (!mid) {
        return -1;
    }
    env->CallStaticVoidMethod(mActivityClass, mid, command, param);
    return 0;
}

extern "C" int Android_JNI_ShowTextInput(SDL_Rect *inputRect)
{
    JNIEnv *env = Android_JNI_GetEnv();
    if (!env) {
        return -1;
    }

    jmethodID mid = env->GetStaticMethodID(mActivityClass, "showTextInput", "(IIII)V");
    if (!mid) {
        return -1;
    }
    env->CallStaticVoidMethod( mActivityClass, mid,
                               inputRect->x,
                               inputRect->y,
                               inputRect->w,
                               inputRect->h );
    return 0;
}

/*extern "C" int Android_JNI_HideTextInput()
{


    JNIEnv *env = Android_JNI_GetEnv();
    if (!env) {
        return -1;
    }

    jmethodID mid = env->GetStaticMethodID(mActivityClass, "hideTextInput", "()V");
    if (!mid) {
        return -1;
    }
    env->CallStaticVoidMethod(mActivityClass, mid);
    return 0;
}*/

#endif /* __ANDROID__ */

/* vi: set ts=4 sw=4 expandtab: */
