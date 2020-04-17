#define NO_BIT_DEFINES
#include <pic14regs.h>
#include <stdint.h>

/* CONFIG1: CONFIGURATION WORD 1 */
__code uint16_t __at (_CONFIG1) __config1 =
	_FOSC_INTOSC &
	_WDTE_OFF &
	_PWRTE_ON &
	_MCLRE_OFF &
	_CP_OFF &
	_BOREN_OFF &
	_CLKOUTEN_OFF;

/*  CONFIG2: CONFIGURATION WORD 2 */
__code uint16_t __at (_CONFIG2) __config2 =
	_WRT_OFF &
	_PLLEN_OFF &
	_STVREN_OFF &
	_BORV_LO &
	_LPBOREN_OFF &
	_DEBUG_OFF &
	_LVP_OFF;

#define DATA_FILTERED		PORTAbits.RA2
#define DATA_FILTERED_TRIS	TRISAbits.TRISA2
#define DATA_FILTERED_OD	ODCONAbits.ODA2

// #define DER			PORTAbits.RA2
// #define DER_TRIS		TRISAbits.TRISA2

#define DATA			PORTAbits.RA5
#define DATA_TRIS		TRISAbits.TRISA5

void main(void)
{
	/* 250 KHz internal clock */
	OSCCON = _IRCF2 | _IRCF1 | _SCS1;

	/* Configure the output */
	DATA_FILTERED_TRIS = 0;   /* output */
	DATA_FILTERED_OD = 1;     /* open-drain */

	/* Configure the input */
	DATA_TRIS = 1;  /* input */

	while (1) {
		DATA_FILTERED = DATA;
	}
}
