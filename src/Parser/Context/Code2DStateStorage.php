<?php
namespace ReceiptPrintHq\EscposTools\Parser\Context;

/* This class implements the internal printer state for 2D code handling. 

It is used to keep the state before printing, since the command codes can be sent in no particular order.

NOTE:  this should be cleared when the "ESC @" command (aka 'InitializeCmd') is processed.

/*  A QR code is sent over a few commands.  Here is the code from python-escpos:

        def qr(
            self,
            content,
            ec=QR_ECLEVEL_L,
            size=3,
            model=QR_MODEL_2,
            native=False,
            center=False,
            impl="bitImageRaster",
        ) -> None:

            # snip, snip: I removed the qr->image conversion which is not useful

            # Native 2D code printing
            cn = b"1"  # Code type for QR code
            # Select model: 1, 2 or micro.
            self._send_2d_code_data(
                six.int2byte(65), cn, six.int2byte(48 + model) + six.int2byte(0)
            )
            # Set dot size.
            self._send_2d_code_data(six.int2byte(67), cn, six.int2byte(size))
            # Set error correction level: L, M, Q, or H
            self._send_2d_code_data(six.int2byte(69), cn, six.int2byte(48 + ec))
            # Send content & print
            self._send_2d_code_data(six.int2byte(80), cn, content.encode("utf-8"), b"0")
            self._send_2d_code_data(six.int2byte(81), cn, b"", b"0")

        def _send_2d_code_data(self, fn, cn, data, m=b"") -> None:
            """Calculate and send correct data length for`GS ( k`.

            :param fn: Function to use.
            :param cn: Output code type. Affects available data.
            :param data: Data to send.
            :param m: Modifier/variant for function. Often '0' where used.
            """
            if len(m) > 1 or len(cn) != 1 or len(fn) != 1:
                raise ValueError("cn and fn must be one byte each.")
            header = self._int_low_high(len(data) + len(m) + 2, 2)
            self._raw(GS + b"(k" + header + cn + fn + m + data)

    So we need to keep everything organized to build a QR visual.

    After that, by using endroid/qr-code, we shoud be able to make an image out of it.

*/
class Code2DStateStorage
{

    public function __construct(private int $qrCodeModel = 50,
                                private int $qrModuleSize = 0,
                                private int $qrErrorCorrectionLevel = 48,
                                private string $symbolStorage = null ){ $this->reset();}

    //To implement the ESC @ reset.
    public function reset(){
        $this->$qrCodeModel = 50;  //50 is the default.
        $this->$qrModuleSize = 0;  //TODO: The specs calls for a printer default.  Choose a sane one.
        $this->qrErrorCorrectionLevel = 48;
        $this->symbolStorage = null;
    }

    //To implement GS ( k <Function 165>,  this sets the QR code model:  49, 50 or 51.
    public function setQRModel($model){
        $x = ord($model);
        if($x === 49 || $x === 50 || $x === 51){
            $this->qrCodeModel = $x;
        }
        //TODO: We should probably return an error if another value is sent.
    }

    //To implement GS ( k <Function 167>, this sets the modulus size
    public function setModuleSize($n){
        $this->qrModuleSize = ord($n);
    }

    //To implement GS ( k <Function 169>, this sets the error correction level
    public function setErrorCorrectLevel($level){
        $x=ord($level);
        if($x === 48 || $x === 49 || $x === 50 || $x === 51){
            $this->qrErrorCorrectionLevel = $x;
        }
        //TODO: We should probably return an error if another value is sent.
    }

    //To implement GS ( k <Function 180>, this stores the QR code data
    public function fillSymbolStorage($data){
        //TODO: We should probably do some bounds-checking to prevent overflowing the data size.
        $this->symbolStorage = $data;
    }

    //To implement GS ( k <Function 182>, Transmit the size information of the symbol data in the symbol storage area
    public function printQRCodeStateInfo(){
        //TODO: implement the status info - this is probably unnecessary for the ESCPOS-netprinter project.
        //Of special interest here is the "Other information" data which states if printing is possible.
    }

    //To implement GS ( k <Function 181>, this outputs the QR code in png format
    public function printQRCode(){
        //TODO:  implement the printing with endroid/qr-code
        /* $qrCode = Builder::create()
                        ->writer(new PngWriter())
                        ->writerOptions([])
                        ->data('Custom QR code contents')
                        ->encoding(new Encoding('UTF-8'))
                        ->errorCorrectionLevel(new ErrorCorrectionLevelHigh())
                        ->size(300)
                        ->margin(10)
                        ->roundBlockSizeMode(new RoundBlockSizeModeMargin())
                        ->logoPath(__DIR__.'/assets/symfony.png')
                        ->logoResizeToWidth(50)
                        ->logoPunchoutBackground(true)
                        ->labelText('This is the label')
                        ->labelFont(new NotoSans(20))
                        ->labelAlignment(new LabelAlignmentCenter())
                        ->validateResult(false)
                        ->build();
            */
            
        }
}