#import "bridge.h"

@implementation bridge

CMAltimeter *altimeterManager;

- (id) init {
    if(self = [super init]) {
        self.motionManager = [[CMMotionManager alloc] init];
        queue = [[NSOperationQueue alloc] init];
    }
    return self;
}

- (void)startAccelerometer {
    
    if ([self.motionManager isAccelerometerAvailable] == YES) {
        [self.motionManager startAccelerometerUpdatesToQueue:queue withHandler:^(CMAccelerometerData *accelerometerData, NSError *error) {
            self.ac_x = accelerometerData.acceleration.x;
            self.ac_y = accelerometerData.acceleration.y;
            self.ac_z = accelerometerData.acceleration.z;
        }];
    }
}

- (void)startGyroscope {
    
    if ([self.motionManager isGyroAvailable] == YES) {
        [self.motionManager startGyroUpdatesToQueue:queue withHandler:^(CMGyroData *gyroData, NSError *error) {
            self.gy_x = gyroData.rotationRate.x;
            self.gy_y = gyroData.rotationRate.y;
            self.gy_z = gyroData.rotationRate.z;
        }];
    }
}

- (void)startMagnetometer {
    
    if (self.motionManager.magnetometerAvailable) {
        [self.motionManager startMagnetometerUpdatesToQueue:queue withHandler:^(CMMagnetometerData *magnetometerData, NSError *error) {
            self.mg_x = magnetometerData.magneticField.x;
            self.mg_y = magnetometerData.magneticField.y;
            self.mg_z = magnetometerData.magneticField.z;
        }];
    }
}

- (void)startDeviceMotion {

    if (self.motionManager.deviceMotionAvailable) {
        [self.motionManager startDeviceMotionUpdatesUsingReferenceFrame:CMAttitudeReferenceFrameXTrueNorthZVertical toQueue:queue withHandler:^(CMDeviceMotion *deviceMotion, NSError *error) {
            self.sp_roll = deviceMotion.attitude.roll;
            self.sp_pitch = deviceMotion.attitude.pitch;
            self.sp_yaw = deviceMotion.attitude.yaw;

            self.g_x = deviceMotion.gravity.x;
            self.g_y = deviceMotion.gravity.y;
            self.g_z = deviceMotion.gravity.z;

            self.rotation_rate_x = deviceMotion.rotationRate.x;
            self.rotation_rate_y = deviceMotion.rotationRate.y;
            self.rotation_rate_z = deviceMotion.rotationRate.z;

            self.user_acc_x = deviceMotion.userAcceleration.x;
            self.user_acc_y = deviceMotion.userAcceleration.y;
            self.user_acc_z = deviceMotion.userAcceleration.z;

            self.q_x = deviceMotion.attitude.quaternion.x;
            self.q_y = deviceMotion.attitude.quaternion.y;
            self.q_z = deviceMotion.attitude.quaternion.z;
            self.q_w = deviceMotion.attitude.quaternion.w;
        }];
    }
}

- (void)startDeviceMotionWithReferenceFrame {

    if (self.motionManager.deviceMotionAvailable) {
        [self.motionManager startDeviceMotionUpdatesUsingReferenceFrame:CMAttitudeReferenceFrameXArbitraryCorrectedZVertical toQueue:queue withHandler:^(CMDeviceMotion *deviceMotion, NSError *error) {
            self.mf_x = deviceMotion.magneticField.field.x;
            self.mf_y = deviceMotion.magneticField.field.y;
            self.mf_z = deviceMotion.magneticField.field.z;
        }];
    }
}

- (void)startRelativeAltitude {

    if ([CMAltimeter isRelativeAltitudeAvailable]) {
        altimeterManager = [[CMAltimeter alloc] init];
        [altimeterManager startRelativeAltitudeUpdatesToQueue:queue withHandler:^(CMAltitudeData *altitudeData, NSError *error) {
            self.relative_altitude = altitudeData.relativeAltitude.floatValue;
            self.pressure = altitudeData.pressure.floatValue;
        }];
    }
}

- (void) stopAccelerometer {
    [self.motionManager stopAccelerometerUpdates];
}

- (void) stopGyroscope {
    [self.motionManager stopGyroUpdates];
}

- (void) stopMagnetometer {
    [self.motionManager stopMagnetometerUpdates];
}

- (void) stopDeviceMotion {
    [self.motionManager stopDeviceMotionUpdates];
}

- (void) stopRelativeAltitude {
    [altimeterManager stopRelativeAltitudeUpdates];
}

- (void) dealloc {
    [self.motionManager release];
    [queue release];
    [super dealloc];
}

@end
