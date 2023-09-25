<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\DataSubCmd;


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

    After that, by using endroid/qr-code, we shoud be able to make an image out of it:

        $qrCode = QrCode::create('Life is too short to be generating QR codes')
            ->setEncoding(new Encoding('UTF-8'))
            ->setErrorCorrectionLevel(new ErrorCorrectionLevelLow())
            ->setSize(300)
            ->setMargin(10)
            ->setRoundBlockSizeMode(new RoundBlockSizeModeMargin())
            ->setForegroundColor(new Color(0, 0, 0))
            ->setBackgroundColor(new Color(255, 255, 255));

*/

class QRcodeSubCommand extends DataSubCmd
{

    private $fn = null;

    public function addChar($char)
    {
        if ($this->fn === null){
            //First extract the QR function
            $this -> fn = ord($char);
            return true;
        }
        else{ 
            //then get [parameters]
            return parent::addChar($char);
        }
    }

}