/*
  Copyright (C) 1997-2011 Sam Lantinga <slouken@libsdl.org>

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the authors be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely.
*/

/* Simple program to test the SDL joystick routines */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "SDL.h"
#include "common.h"

static CommonState *state;
static SDL_BlendMode blendMode = SDL_BLENDMODE_NONE;

#define MAX_NUM_AXES 6
#define MAX_NUM_HATS 2

static void
DrawRect(SDL_Renderer *r, const int x, const int y, const int w, const int h)
{
    const SDL_Rect area = { x, y, w, h };
    SDL_RenderFillRect(r, &area);
}

void
WatchJoystick(SDL_Joystick * joystick)
{
    SDL_Window *window = NULL;
    SDL_Renderer *screen = NULL;
    SDL_Rect viewport;
    SDL_Event event;

    const char *name = NULL;
    int done = 0;
    int i;

    /* Print info about the joystick we are watching */
    name = SDL_JoystickName(SDL_JoystickIndex(joystick));
    printf("Watching joystick %d: (%s)\n", SDL_JoystickIndex(joystick),
           name ? name : "Unknown Joystick");
    printf("Joystick has %d axes, %d hats, %d balls, and %d buttons\n",
           SDL_JoystickNumAxes(joystick), SDL_JoystickNumHats(joystick),
           SDL_JoystickNumBalls(joystick), SDL_JoystickNumButtons(joystick));

    /* Loop, getting joystick events! */
    while (!done) {
        while (SDL_PollEvent(&event)) {
            switch (event.type) {
            case SDL_JOYAXISMOTION:
                printf("Joystick %d axis %d value: %d\n",
                       event.jaxis.which,
                       event.jaxis.axis, event.jaxis.value);
                break;
            case SDL_JOYHATMOTION:
                printf("Joystick %d hat %d value:",
                       event.jhat.which, event.jhat.hat);
                if (event.jhat.value == SDL_HAT_CENTERED)
                    printf(" centered");
                if (event.jhat.value & SDL_HAT_UP)
                    printf(" up");
                if (event.jhat.value & SDL_HAT_RIGHT)
                    printf(" right");
                if (event.jhat.value & SDL_HAT_DOWN)
                    printf(" down");
                if (event.jhat.value & SDL_HAT_LEFT)
                    printf(" left");
                printf("\n");
                break;
            case SDL_JOYBALLMOTION:
                printf("Joystick %d ball %d delta: (%d,%d)\n",
                       event.jball.which,
                       event.jball.ball, event.jball.xrel, event.jball.yrel);
                break;
            case SDL_JOYBUTTONDOWN:
                printf("Joystick %d button %d down\n",
                       event.jbutton.which, event.jbutton.button);
                break;
            case SDL_JOYBUTTONUP:
                printf("Joystick %d button %d up\n",
                       event.jbutton.which, event.jbutton.button);
                break;
            case SDL_KEYDOWN:
                if (event.key.keysym.sym != SDLK_ESCAPE) {
                    break;
                }
                /* Fall through to signal quit */
            case SDL_QUIT:
                done = 1;
                break;
            default:
                break;
            }
        }

        /* Update visual joystick state */
        for (i = 0; i < state->num_windows; ++i) {
            screen = state->renderers[i];

            /* Erase previous axes */
            SDL_SetRenderDrawColor(screen, 0x00, 0x00, 0x00, SDL_ALPHA_OPAQUE);
            SDL_RenderClear(screen);

            /* Query the sizes */
            SDL_RenderGetViewport(screen, &viewport);

            SDL_SetRenderDrawColor(screen, 0x00, 0xFF, 0x00, SDL_ALPHA_OPAQUE);
            for (i = 0; i < SDL_JoystickNumButtons(joystick); ++i) {
                if (SDL_JoystickGetButton(joystick, i) == SDL_PRESSED) {
                    DrawRect(screen, i * 34, viewport.h - 34, 32, 32);
                }
            }

            SDL_SetRenderDrawColor(screen, 0xFF, 0x00, 0x00, SDL_ALPHA_OPAQUE);
            for (i = 0; i < SDL_JoystickNumAxes(joystick) / 2; ++i) {
                /* Draw the X/Y axis */
                int x, y;
                x = (((int) SDL_JoystickGetAxis(joystick, i * 2 + 0)) + 32768);
                x *= viewport.w ;
                x /= 65535;
                if (x < 0) {
                    x = 0;
                } else if (x > (viewport.w - 16)) {
                    x = viewport.w - 16;
                }
                y = (((int) SDL_JoystickGetAxis(joystick, i * 2 + 1)) + 32768);
                y *= viewport.h;
                y /= 65535;
                if (y < 0) {
                    y = 0;
                } else if (y > (viewport.h - 16)) {
                    y = viewport.h - 16;
                }

                DrawRect(screen, x, y, 16, 16);
            }

            SDL_SetRenderDrawColor(screen, 0x00, 0x00, 0xFF, SDL_ALPHA_OPAQUE);
            for (i = 0; i < SDL_JoystickNumHats(joystick); ++i) {
                /* Derive the new position */
                int x = viewport.w/2;
                int y = viewport.h/2;
                const Uint8 hat_pos = SDL_JoystickGetHat(joystick, i);

                if (hat_pos & SDL_HAT_UP) {
                    y = 0;
                } else if (hat_pos & SDL_HAT_DOWN) {
                    y = viewport.h-8;
                }

                if (hat_pos & SDL_HAT_LEFT) {
                    x = 0;
                } else if (hat_pos & SDL_HAT_RIGHT) {
                    x = viewport.w-8;
                }

                DrawRect(screen, x, y, 8, 8);
            }

            SDL_RenderPresent(screen);
        }
    }
}

int
main(int argc, char *argv[])
{
    const char *name;
    int i, joy=-1;
    SDL_Joystick *joystick;

    /* Initialize SDL (Note: video is required to start event loop) */
    if (SDL_Init(SDL_INIT_JOYSTICK) < 0) {
        fprintf(stderr, "Couldn't initialize SDL: %s\n", SDL_GetError());
        exit(1);
    }

    /* Initialize test framework */
    state = CommonCreateState(argv, SDL_INIT_VIDEO | SDL_INIT_JOYSTICK);
    if (!state) {
        fprintf(stderr, "Couldn't initialize SDL: %s\n", SDL_GetError());
        return 1;
    }

    /* Print information about the joysticks */
    printf("There are %d joysticks attached\n", SDL_NumJoysticks());
    for (i = 0; i < SDL_NumJoysticks(); ++i) {
        name = SDL_JoystickName(i);
        printf("Joystick %d: %s\n", i, name ? name : "Unknown Joystick");
        joystick = SDL_JoystickOpen(i);
        if (joystick == NULL) {
            fprintf(stderr, "SDL_JoystickOpen(%d) failed: %s\n", i,
                    SDL_GetError());
        } else {
            printf("       axes: %d\n", SDL_JoystickNumAxes(joystick));
            printf("      balls: %d\n", SDL_JoystickNumBalls(joystick));
            printf("       hats: %d\n", SDL_JoystickNumHats(joystick));
            printf("    buttons: %d\n", SDL_JoystickNumButtons(joystick));
            SDL_JoystickClose(joystick);
        }
    }

    for (i = 1; i < argc;) {
        int consumed;

        consumed = CommonArg(state, i);
        if (consumed == 0) {
            consumed = -1;
            if (SDL_isdigit(*argv[i])) {
                joy = SDL_atoi(argv[i]);
                consumed = 1;
            }
        }
        if (consumed < 0) {
            return 1;
        }
        i += consumed;
    }
    if (!CommonInit(state)) {
        return 2;
    }

    if (joy > -1) {
        joystick = SDL_JoystickOpen(joy);
        if (joystick == NULL) {
            printf("Couldn't open joystick %d: %s\n", joy,
                   SDL_GetError());
        } else {
            WatchJoystick(joystick);
            SDL_JoystickClose(joystick);
        }
    }
    SDL_QuitSubSystem(SDL_INIT_JOYSTICK);
    CommonQuit(state);

    return (0);
}
