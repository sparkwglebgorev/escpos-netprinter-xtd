<?php
namespace ReceiptPrintHq\EscposTools\Parser\Command;

use ReceiptPrintHq\EscposTools\Parser\Command\Code2DSubCommand;
use ReceiptPrintHq\EscposTools\Parser\Command\DataCmd;
use ReceiptPrintHq\EscposTools\Parser\Command\QRCodeSubCommand;
use ReceiptPrintHq\EscposTools\Parser\Command\UnimplementedCode2DSubCommand;

// This interprets the "GS ( k" commands. 
// Official Description: Performs data processing related to 2-dimensional codes 
//                       (PDF417, QR Code, MaxiCode, 2-dimensional GS1 DataBar, Composite Symbology). 
class Code2DDataCmd extends DataCmd
{
    /*This symbol has the following format: GS ( k pL pH cn fn [parameters]
    Symbol type is specified by cn
    Function code fn specifies the function
    pL and pH specify the number of bytes following cn as (pL + pH × 256)
    The [parameters] are described in each function. 
    (ref: Epson ESC/POS Command Reference for TM Printers)
    */
    private $pL = null;
    private $pH = null;
    private $cn = null;
    private ?Code2DSubCommand $subCommand = null;
  
    //Process one command byte.  Return true if the byte is interpreted without error
    public function addChar($char)
    {
        //Lets begin by getting the size from the first 4 bytes
        if ($this -> pL === null){
            $this -> pL = ord($char);
            return true;
        }
        elseif ($this -> pH === null){
            $this -> pH = ord($char);
            //Calculate the length of fn+[parameters] - the spec counts cn, so we remove its size
            $this->dataSize = ($this->pL + $this->pH * 256) - 1;  
            return true;
        }
        //Now interpret the subcommand
        elseif ($this->cn === null) {
            $this -> cn = ord($char);

            //If the command is known, assign subCommand with the interpreter class
            if($this->cn == 48){
                //this is a PDF417 code command
                $this->subCommand = new UnimplementedCode2DSubCommand($this->dataSize) ;
            }
            elseif($this->cn == 49){
                //this is a QR code command
                $this->subCommand = new QRCodeSubCommand($this->dataSize);
                //$this->subCommand = new UnimplementedCode2DSubCommand($this->dataSize) ;
            }
            elseif($this->cn >= 50 && $this->cn <= 54) {
                //this is one of the other valid codes
                $this->subCommand = new UnimplementedCode2DSubCommand($this->dataSize) ;
            }
            else{
                error_log("Invalid QR code subfunction received: " . ord($char) . "",0);
                $this->subCommand = new Code2DSubCommand($this->dataSize);  //fill sub with a placeholder
            }
            return true;
        }
        else  { //Process everything after cn
                //Send the fn and parameter data to the subcommand
                return $this->subCommand->addChar($char);
        }
    }

    public function subCommand()
    {
        // TODO rename and take getSubCommand() name.
        return $this -> subCommand;
    }
    
}
