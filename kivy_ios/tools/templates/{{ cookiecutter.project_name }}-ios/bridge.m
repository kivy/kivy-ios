#import "bridge.h"

@implementation bridge

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

- (void) stopAccelerometer {
    [self.motionManager stopAccelerometerUpdates];
}

- (void) stopGyroscope {
    [self.motionManager stopGyroUpdates];
}

- (void) stopMagnetometer {
    [self.motionManager stopMagnetometerUpdates];
}

- (void) dealloc {
    [self.motionManager release];
    [queue release];
    [super dealloc];
}

@end
